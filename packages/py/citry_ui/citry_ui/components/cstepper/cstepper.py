"""Ordered workflow progress and optional step navigation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, cast

from citry import CitryRender, LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CStepperOrientation = Literal["horizontal", "vertical"]
CStepperVariant = Literal["plain", "soft", "outline"]
CStepperSize = Literal["sm", "md", "lg"]
CStepState = Literal["complete", "current", "upcoming"]

_ORIENTATIONS = ("horizontal", "vertical")
_VARIANTS = ("plain", "soft", "outline")
_SIZES = ("sm", "md", "lg")
_STEPPER_CONTEXT = "citry_ui_stepper"
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "contenteditable",
        "data-active",
        "data-citry-ui-part",
        "data-disabled",
        "data-interactive",
        "data-linear",
        "data-orientation",
        "data-size",
        "data-variant",
        "hidden",
        "inert",
        "role",
        "tabindex",
    }
)
_STEP_OWNED = frozenset(
    {
        "aria-current",
        "aria-describedby",
        "aria-hidden",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-error",
        "data-index",
        "data-optional",
        "data-state",
        "disabled",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
        "type",
    }
)


class CStepperDefaultSlotData:
    pass


class CStepDefaultSlotData(TypedDict):
    index: int
    state: CStepState
    is_current: bool
    is_disabled: bool


class CStepDescriptionSlotData(CStepDefaultSlotData):
    pass


class CStepIndicatorSlotData(CStepDefaultSlotData):
    pass


class CStepperActiveChangeDetail(TypedDict):
    active: int
    previousActive: int
    controlled: bool
    step: object
    sourceEvent: object


@dataclass(frozen=True, slots=True)
class _StepDeclaration:
    disabled: bool
    optional: bool
    error: bool
    attrs: dict[str, object]
    label: Slot[CStepDefaultSlotData]
    description: Slot[CStepDescriptionSlotData] | None
    indicator: Slot[CStepIndicatorSlotData] | None


@dataclass(slots=True)
class _StepperRegistry:
    steps: list[_StepDeclaration] = field(default_factory=list)


def _plain(name: str, value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        raise TypeError(f"CStepper {name} must be a string, got {raw!r}.")
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip() or "\x00" in plain:
        raise ValueError(f"CStepper {name} must be nonempty and cannot contain U+0000.")
    return plain


def _choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        raise ValueError(f"CStepper {name} must be one of {expected}, got {plain!r}.")
    return plain


def _active(value: object) -> int:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError(f"CStepper active must be a nonnegative integer, got {raw!r}.")
    if raw < 0:
        raise ValueError(f"CStepper active must be nonnegative, got {raw!r}.")
    return raw


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


def _context(component: LibraryComponent) -> _StepperRegistry:
    context = component.inject(_STEPPER_CONTEXT, None)
    if context is None:
        raise ValueError("CStep is a declaration component and must be rendered directly inside CStepper.")
    return cast("_StepperRegistry", context.registry)


def _validate_declaration_output(result: CitryRender) -> None:
    if result.serialize(deps_strategy="ignore").strip():
        raise ValueError(
            "CStepper default content may contain only CStep declarations, formatting whitespace, "
            "and transparent components that produce no other output."
        )


class CStepper(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        active: int = 0
        interactive: bool = False
        linear: bool = True
        disabled: bool = False
        orientation: CStepperOrientation = "horizontal"
        variant: CStepperVariant = "plain"
        size: CStepperSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CStepperDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        if self.inject(_STEPPER_CONTEXT, None) is not None:
            raise ValueError(
                "Nested CStepper must be rendered inside CStep content, not as a direct Step declaration."
            )
        label = _plain("label", kwargs.label)
        active = _active(kwargs.active)
        for name in ("interactive", "linear", "disabled"):
            validate_boolean("CStepper", name, getattr(kwargs, name))
        orientation = _choice("orientation", kwargs.orientation, _ORIENTATIONS)
        variant = _choice("variant", kwargs.variant, _VARIANTS)
        size = _choice("size", kwargs.size, _SIZES)
        if "default" not in self.raw_slots:
            raise ValueError("CStepper requires a default slot with at least two CStep declarations.")
        registry = _StepperRegistry()
        self.provide(_STEPPER_CONTEXT, registry=registry)
        data = {
            "label": label,
            "active": active,
            "interactive": bool(kwargs.interactive),
            "linear": bool(kwargs.linear),
            "disabled": bool(kwargs.disabled),
            "orientation": orientation,
            "variant": variant,
            "size": size,
        }
        self._stepper_data = data
        return {
            **data,
            "attrs": _attrs("CStepper", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "registry": registry,
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return self._stepper_data

    template = """
      <c-CInternalStepperDeclarations><c-slot required /></c-CInternalStepperDeclarations>
      <c-CInternalStepper
        c-label="label"
        c-active="active"
        c-interactive="interactive"
        c-linear="linear"
        c-disabled="disabled"
        c-orientation="orientation"
        c-variant="variant"
        c-size="size"
        c-attrs="attrs"
        c-registry="registry"
      />
    """

    js = r"""
      $component({
        props: {active: {}, linear: {}, disabled: {}, orientation: {}, variant: {}, size: {}, onActiveChange: {}},
        init: ({els, data, props, effect}) => {
          const root = els[0];
          const stepSelector = ':scope > [data-citry-ui-part="list"] > [data-citry-ui-part="step"]';
          const invalidEpisodes = new Set();
          const prior = root.__citryUiStepperRuntime;
          let committed = prior && prior.serverActive === data.active ? prior.committed : data.active;
          let current = committed;
          let controlled = false;
          let callback = null;
          let configuration = {
            linear: data.linear,
            disabled: data.disabled,
            orientation: data.orientation,
            variant: data.variant,
            size: data.size,
          };
          let generation = 0;
          let task = null;
          let structureValid = false;

          const report = (name, value) => {
            if (invalidEpisodes.has(name)) return;
            invalidEpisodes.add(name);
            console.error(`[citry-ui] CStepper ${name} received invalid client value`, value);
          };
          const resolveBoolean = (name, fallback) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'boolean') { invalidEpisodes.delete(name); return supplied; }
            report(name, supplied);
            return fallback;
          };
          const resolveChoice = (name, fallback, allowed) => {
            const supplied = props[name];
            if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
            if (typeof supplied === 'string' && allowed.includes(supplied)) {
              invalidEpisodes.delete(name);
              return supplied;
            }
            report(name, supplied);
            return fallback;
          };
          const steps = () => [...root.querySelectorAll(stepSelector)];
          const trigger = (step) => step.querySelector(':scope > [data-citry-ui-part="trigger"]');
          const invalidStructure = (entries) => {
            if (entries.length < 2) return `expected at least two Steps, got ${entries.length}`;
            for (const [index, step] of entries.entries()) {
              if (Number(step.dataset.index) !== index) return 'Step indices do not match settled order';
              const control = trigger(step);
              if (!(control instanceof Element)) return `Step ${index} has no owned trigger`;
              const nested = control.querySelector(
                'a[href], button, input, select, textarea, '
                + '[contenteditable]:not([contenteditable="false"]), [tabindex]'
              );
              if (nested) return `Step ${index} label contains an interactive descendant`;
            }
            return null;
          };
          const normalizeFailed = (entries) => {
            root.removeAttribute('data-citry-stepper-initialized');
            entries.forEach((step) => {
              const control = trigger(step);
              if (control instanceof HTMLButtonElement) control.disabled = true;
            });
          };
          const sync = () => {
            const entries = steps();
            const problem = invalidStructure(entries);
            if (problem) {
              structureValid = false;
              report('structure', problem);
              normalizeFailed(entries);
              return;
            }
            invalidEpisodes.delete('structure');
            structureValid = true;
            if (!Number.isInteger(committed) || committed < 0 || committed >= entries.length) {
              committed = Math.max(0, Math.min(entries.length - 1, Number.isInteger(committed) ? committed : 0));
            }
            let requested = props.active;
            if (requested === null) requested = undefined;
            if (requested === undefined) {
              invalidEpisodes.delete('active');
              if (controlled) committed = current;
              controlled = false;
              current = committed;
            } else if (Number.isInteger(requested) && requested >= 0 && requested < entries.length) {
              invalidEpisodes.delete('active');
              controlled = true;
              current = requested;
            } else {
              report('active', requested);
              controlled = true;
              current = committed;
            }
            root.dataset.active = String(current);
            root.dataset.orientation = configuration.orientation;
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            root.toggleAttribute('data-linear', configuration.linear);
            root.toggleAttribute('data-disabled', configuration.disabled);
            entries.forEach((step, index) => {
              const control = trigger(step);
              const state = index < current ? 'complete' : index === current ? 'current' : 'upcoming';
              const ownDisabled = step.hasAttribute('data-own-disabled');
              const unavailable = configuration.disabled || ownDisabled || (configuration.linear && index > current);
              step.dataset.state = state;
              step.toggleAttribute('data-disabled', unavailable || (control.matches?.(':disabled') ?? false));
              control.toggleAttribute('aria-current', index === current);
              if (index === current) control.setAttribute('aria-current', 'step');
              if (control instanceof HTMLButtonElement) control.disabled = unavailable;
            });
            root.setAttribute('data-citry-stepper-initialized', '');
            root.__citryUiStepperRuntime = {serverActive: data.active, committed};
          };
          const schedule = () => {
            if (task !== null) return;
            const scheduled = generation;
            task = setTimeout(() => {
              task = null;
              if (scheduled === generation) sync();
            }, 0);
          };
          const onClick = (event) => {
            if (!structureValid) return;
            const control = event.composedPath().find(
              (node) => node instanceof Element && node.matches?.('[data-citry-ui-part="trigger"]')
            );
            if (!(control instanceof HTMLButtonElement) || control.disabled || control.matches(':disabled')) return;
            const step = control.closest('[data-citry-ui-part="step"]');
            if (!step || step.closest('[data-citry-ui-part="stepper"]') !== root) return;
            const next = Number(step.dataset.index);
            if (!Number.isInteger(next) || next === current) return;
            const previousActive = current;
            callback?.(next, {active: next, previousActive, controlled, step, sourceEvent: event});
            if (!controlled) { committed = next; current = next; sync(); }
            else schedule();
          };
          const observer = new MutationObserver((records) => {
            if (records.every((record) => record.attributeName === 'disabled'
                && record.target instanceof HTMLButtonElement)) return;
            schedule();
          });
          observer.observe(root, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: ['contenteditable', 'href', 'tabindex', 'type'],
          });
          const fieldsets = [];
          for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (!(ancestor instanceof HTMLFieldSetElement)) continue;
            const item = new MutationObserver(schedule);
            item.observe(ancestor, {attributes: true, childList: true, attributeFilter: ['disabled']});
            fieldsets.push(item);
          }
          root.addEventListener('click', onClick);
          const stop = effect(() => {
            callback = typeof props.onActiveChange === 'function' ? props.onActiveChange : null;
            configuration = {
              linear: resolveBoolean('linear', data.linear),
              disabled: resolveBoolean('disabled', data.disabled),
              orientation: resolveChoice('orientation', data.orientation, ['horizontal', 'vertical']),
              variant: resolveChoice('variant', data.variant, ['plain', 'soft', 'outline']),
              size: resolveChoice('size', data.size, ['sm', 'md', 'lg']),
            };
            schedule();
          });
          schedule();
          return () => {
            generation += 1;
            if (task !== null) clearTimeout(task);
            root.__citryUiStepperRuntime = {serverActive: data.active, committed};
            stop?.();
            observer.disconnect();
            fieldsets.forEach((item) => item.disconnect());
            root.removeEventListener('click', onClick);
            root.removeAttribute('data-citry-stepper-initialized');
          };
        },
      })
    """

    css_file = "runtime.min.css"


class CStep(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        disabled: bool = False
        optional: bool = False
        error: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CStepDefaultSlotData]
        description: SlotInput[CStepDescriptionSlotData] | None = None
        indicator: SlotInput[CStepIndicatorSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        for name in ("disabled", "optional", "error"):
            validate_boolean("CStep", name, getattr(kwargs, name))
        if "default" not in self.raw_slots:
            raise ValueError("CStep requires a default label slot.")
        registry = _context(self)
        registry.steps.append(
            _StepDeclaration(
                disabled=bool(kwargs.disabled),
                optional=bool(kwargs.optional),
                error=bool(kwargs.error),
                attrs=_attrs("CStep", kwargs.attrs, _STEP_OWNED, kwargs.class_, kwargs.style),
                label=cast("Slot[CStepDefaultSlotData]", slots.default),
                description=cast("Slot[CStepDescriptionSlotData] | None", slots.description),
                indicator=cast("Slot[CStepIndicatorSlotData] | None", slots.indicator),
            )
        )
        self.unprovide(_STEPPER_CONTEXT)
        return {}

    def on_render(self) -> str:
        return ""


class CInternalStepperDeclarations(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CStepperDefaultSlotData]

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CStepper declaration collection completed without a render result.")
        _validate_declaration_output(result)

    template = "<c-slot required />"


class CInternalStepper(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        label: str
        active: int
        interactive: bool
        linear: bool
        disabled: bool
        orientation: CStepperOrientation
        variant: CStepperVariant
        size: CStepperSize
        attrs: dict[str, object]
        registry: _StepperRegistry

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        if len(kwargs.registry.steps) < 2:
            raise ValueError("CStepper requires at least two CStep declarations.")
        if kwargs.active >= len(kwargs.registry.steps):
            raise ValueError(
                f"CStepper active index {kwargs.active} is outside {len(kwargs.registry.steps)} declared Steps."
            )
        if kwargs.registry.steps[kwargs.active].disabled:
            raise ValueError(f"CStepper active index {kwargs.active} identifies a disabled Step.")
        self.unprovide(_STEPPER_CONTEXT)
        root_attrs = {
            **kwargs.attrs,
            "aria-label": kwargs.label,
            "data-active": kwargs.active,
            "data-interactive": kwargs.interactive,
            "data-linear": kwargs.linear,
            "data-disabled": kwargs.disabled,
            "data-orientation": kwargs.orientation,
            "data-variant": kwargs.variant,
            "data-size": kwargs.size,
        }
        return {
            "active": kwargs.active,
            "interactive": kwargs.interactive,
            "linear": kwargs.linear,
            "root_disabled": kwargs.disabled,
            "attrs": root_attrs,
            "steps": [
                {"declaration": declaration, "index": index} for index, declaration in enumerate(kwargs.registry.steps)
            ],
            "count": len(kwargs.registry.steps),
        }

    template = """
      <nav class="cui-stepper" c-bind="attrs" data-citry-ui-part="stepper">
        <ol class="cui-stepper__list" data-citry-ui-part="list">
          <c-for each="step in steps">
            <c-CInternalStep
              c-declaration="step['declaration']"
              c-index="step['index']"
              c-count="count"
              c-active="active"
              c-interactive="interactive"
              c-linear="linear"
              c-root_disabled="root_disabled"
            />
          </c-for>
        </ol>
      </nav>
    """


class CInternalStep(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        declaration: _StepDeclaration
        index: int
        count: int
        active: int
        interactive: bool
        linear: bool
        root_disabled: bool

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        declaration = kwargs.declaration
        state: CStepState = (
            "complete" if kwargs.index < kwargs.active else "current" if kwargs.index == kwargs.active else "upcoming"
        )
        unavailable = declaration.disabled or kwargs.root_disabled or (kwargs.linear and kwargs.index > kwargs.active)
        slot_data: CStepDefaultSlotData = {
            "index": kwargs.index,
            "state": state,
            "is_current": kwargs.index == kwargs.active,
            "is_disabled": unavailable,
        }
        description_id = f"cui-stepper-{self.id}-description" if declaration.description is not None else None
        self.unprovide(_STEPPER_CONTEXT)
        return {
            "morph_key": f"step-{kwargs.index}",
            "attrs": {
                **declaration.attrs,
                "data-index": kwargs.index,
                "data-state": state,
                "data-own-disabled": declaration.disabled,
                "data-disabled": unavailable,
                "data-optional": declaration.optional,
                "data-error": declaration.error,
            },
            "interactive": kwargs.interactive,
            "unavailable": unavailable,
            "current": kwargs.index == kwargs.active,
            "index": kwargs.index,
            "description_id": description_id,
            "label": Slot(lambda ctx: declaration.label(slot_data, provides=dict(ctx.provides or {}))),
            "description": (
                Slot(lambda ctx: declaration.description(slot_data, provides=dict(ctx.provides or {})))
                if declaration.description is not None
                else None
            ),
            "indicator": (
                Slot(lambda ctx: declaration.indicator(slot_data, provides=dict(ctx.provides or {})))
                if declaration.indicator is not None
                else None
            ),
            "last": kwargs.index == kwargs.count - 1,
        }

    template = """
      <li class="cui-stepper__step" #c-key="morph_key" c-bind="attrs" data-citry-ui-part="step">
        <c-if cond="interactive">
          <button
            class="cui-stepper__trigger"
            type="button"
            c-disabled="unavailable"
            c-aria-current="'step' if current else None"
            c-aria-describedby="description_id"
            data-citry-ui-part="trigger"
          >
            <span class="cui-stepper__indicator" aria-hidden="true" data-citry-ui-part="indicator">
              <c-if cond="indicator is not None">{{ indicator }}</c-if><c-else>{{ index + 1 }}</c-else>
            </span>
            <span class="cui-stepper__copy" data-citry-ui-part="copy">
              <span class="cui-stepper__label" data-citry-ui-part="label">{{ label }}</span>
              <c-if cond="description is not None">
                <span
                  class="cui-stepper__description"
                  c-id="description_id"
                  data-citry-ui-part="description"
                >{{ description }}</span>
              </c-if>
            </span>
          </button>
        </c-if>
        <c-else>
          <span
            class="cui-stepper__trigger"
            c-aria-current="'step' if current else None"
            c-aria-describedby="description_id"
            data-citry-ui-part="trigger"
          >
            <span class="cui-stepper__indicator" aria-hidden="true" data-citry-ui-part="indicator">
              <c-if cond="indicator is not None">{{ indicator }}</c-if><c-else>{{ index + 1 }}</c-else>
            </span>
            <span class="cui-stepper__copy" data-citry-ui-part="copy">
              <span class="cui-stepper__label" data-citry-ui-part="label">{{ label }}</span>
              <c-if cond="description is not None">
                <span
                  class="cui-stepper__description"
                  c-id="description_id"
                  data-citry-ui-part="description"
                >{{ description }}</span>
              </c-if>
            </span>
          </span>
        </c-else>
        <c-if cond="not last">
          <span
            class="cui-stepper__separator"
            aria-hidden="true"
            data-citry-ui-part="separator"
          ></span>
        </c-if>
      </li>
    """


__all__ = [
    "CStep",
    "CStepDefaultSlotData",
    "CStepDescriptionSlotData",
    "CStepIndicatorSlotData",
    "CStepState",
    "CStepper",
    "CStepperActiveChangeDetail",
    "CStepperDefaultSlotData",
    "CStepperOrientation",
    "CStepperSize",
    "CStepperVariant",
]
