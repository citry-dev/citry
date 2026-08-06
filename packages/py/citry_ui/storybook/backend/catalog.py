"""One Python-owned catalog projected through both Storybook adapters."""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

from backend.components import CReactiveCounterProbe, CStaticTabsContent
from citry import ComponentLike
from citry_ui import (
    CButton,
    CField,
    CInput,
    CTable,
    CTableColumn,
    CTableRow,
    CTabs,
)

ArgValue = str | bool
ControlKind = Literal["boolean", "select", "text"]
ScenarioRenderer = Callable[[Mapping[str, ArgValue]], ComponentLike]

CATALOG_SCHEMA_VERSION = 1
_SCENARIO_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*$")


class ScenarioArgsError(ValueError):
    """Report invalid or unknown values sent to a scenario."""


@dataclass(frozen=True, slots=True)
class Control:
    name: str
    kind: ControlKind
    default: ArgValue
    description: str
    options: tuple[str, ...] = ()

    def parse(self, raw: str) -> ArgValue:
        if self.kind == "boolean":
            normalized = raw.lower()
            if normalized == "true":
                return True
            if normalized == "false":
                return False
            msg = f"Argument {self.name!r} must be 'true' or 'false'."
            raise ScenarioArgsError(msg)
        if self.kind == "select" and raw not in self.options:
            rendered = ", ".join(repr(option) for option in self.options)
            msg = f"Argument {self.name!r} must be one of {rendered}."
            raise ScenarioArgsError(msg)
        return raw

    def storybook_arg_type(self) -> dict[str, object]:
        value: dict[str, object] = {
            "control": {"type": self.kind},
            "description": self.description,
        }
        if self.options:
            value["options"] = list(self.options)
        return value


@dataclass(frozen=True, slots=True)
class StorybookScenario:
    id: str
    title: str
    group: str
    description: str
    usage: str
    controls: tuple[Control, ...]
    renderer: ScenarioRenderer
    client_interactive: bool = False
    ready_selector: str | None = None
    ready_timeout_ms: int = 10_000

    def __post_init__(self) -> None:
        if _SCENARIO_ID_RE.fullmatch(self.id) is None:
            msg = f"Scenario ID {self.id!r} is not a stable two-segment path."
            raise ValueError(msg)
        names = [control.name for control in self.controls]
        if len(names) != len(set(names)):
            msg = f"Scenario {self.id!r} has duplicate control names."
            raise ValueError(msg)
        if self.client_interactive != (self.ready_selector is not None):
            msg = f"Scenario {self.id!r} must pair client_interactive with one readiness selector."
            raise ValueError(msg)
        if self.ready_timeout_ms <= 0:
            msg = f"Scenario {self.id!r} must define a positive readiness timeout."
            raise ValueError(msg)

    @property
    def args(self) -> dict[str, ArgValue]:
        return {control.name: control.default for control in self.controls}

    @property
    def arg_types(self) -> dict[str, object]:
        return {control.name: control.storybook_arg_type() for control in self.controls}

    def parse_query(self, query: Mapping[str, tuple[str, ...]]) -> dict[str, ArgValue]:
        controls = {control.name: control for control in self.controls}
        unknown = sorted(set(query) - controls.keys())
        if unknown:
            msg = f"Unknown argument(s) for {self.id!r}: {', '.join(unknown)}."
            raise ScenarioArgsError(msg)

        values = self.args
        for name, raw_values in query.items():
            if len(raw_values) != 1:
                msg = f"Argument {name!r} must be provided exactly once."
                raise ScenarioArgsError(msg)
            values[name] = controls[name].parse(raw_values[0])
        return values

    def render(self, args: Mapping[str, ArgValue]) -> ComponentLike:
        return self.renderer(args)


def _bool(args: Mapping[str, ArgValue], name: str) -> bool:
    value = args[name]
    if not isinstance(value, bool):
        msg = f"Internal scenario argument {name!r} is not a bool."
        raise TypeError(msg)
    return value


def _str(args: Mapping[str, ArgValue], name: str) -> str:
    value = args[name]
    if not isinstance(value, str):
        msg = f"Internal scenario argument {name!r} is not a string."
        raise TypeError(msg)
    return value


def _render_button(args: Mapping[str, ArgValue]) -> ComponentLike:
    return CButton(
        loading=_bool(args, "loading"),
        disabled=_bool(args, "disabled"),
        type=_str(args, "type"),
        slots={"default": _str(args, "label")},
    )


def _render_field(args: Mapping[str, ArgValue]) -> ComponentLike:
    invalid = _bool(args, "invalid")
    field_slots: dict[str, object] = {
        "label": _str(args, "label"),
        "default": CInput(
            name="storybook-field",
            type="email",
            value=_str(args, "value"),
        ),
        "description": "This address is used for account notifications.",
    }
    if invalid:
        field_slots["error"] = "Enter a valid email address."
    return CField(
        required=_bool(args, "required"),
        disabled=_bool(args, "disabled"),
        readonly=_bool(args, "readonly"),
        invalid=invalid,
        orientation=_str(args, "orientation"),
        density=_str(args, "density"),
        slots=field_slots,
    )


def _render_table(args: Mapping[str, ArgValue]) -> ComponentLike:
    return CTable(
        columns=(
            CTableColumn("name", "Project", row_header=True),
            CTableColumn("status", "Status"),
            CTableColumn("action", "Action"),
        ),
        rows=(
            CTableRow(
                "citry",
                {
                    "name": "Citry",
                    "status": "Active",
                    "action": CButton(slots={"default": "Open"}),
                },
            ),
            CTableRow(
                "docs",
                {
                    "name": "Documentation",
                    "status": "Draft",
                    "action": CButton(slots={"default": "Review"}),
                },
            ),
        ),
        state=_str(args, "state"),
        density=_str(args, "density"),
        striped=_bool(args, "striped"),
        hover=_bool(args, "hover"),
        sticky_header=_bool(args, "sticky_header"),
        slots={
            "caption": "Projects",
            "loading": "Loading projects",
            "error": "Unable to load projects",
        },
    )


def _render_tabs(args: Mapping[str, ArgValue]) -> ComponentLike:
    return CTabs(
        default_value=_str(args, "selected"),
        aria_label="Account settings",
        orientation=_str(args, "orientation"),
        direction=_str(args, "direction"),
        activation=_str(args, "activation"),
        slots={"default": CStaticTabsContent()},
    )


def _render_reactive_probe(args: Mapping[str, ArgValue]) -> ComponentLike:
    generation = _str(args, "generation")
    if generation == "slow":
        time.sleep(0.8)
    return CReactiveCounterProbe(generation=generation)


SCENARIOS = (
    StorybookScenario(
        id="button/static",
        title="Static",
        group="Button",
        description="Styled button states rendered by Python.",
        usage="""from citry_ui import CButton

button = CButton(
    slots={"default": "Save changes"},
)""",
        controls=(
            Control("label", "text", "Save changes", "Visible button label."),
            Control("loading", "boolean", default=False, description="Show the loading state."),
            Control("disabled", "boolean", default=False, description="Disable the native button."),
            Control("type", "select", "button", "Native button type.", ("button", "submit", "reset")),
        ),
        renderer=_render_button,
    ),
    StorybookScenario(
        id="field/static",
        title="Static",
        group="Field and Input",
        description="Field relationships, validation, layout, and Input composition.",
        usage="""from citry_ui import CField, CInput

field = CField(
    required=True,
    slots={
        "label": "Email address",
        "default": CInput(name="email", type="email"),
        "description": "Used for account notifications.",
    },
)""",
        controls=(
            Control("label", "text", "Email address", "Visible field label."),
            Control("value", "text", "person@example.com", "Native input value."),
            Control("required", "boolean", default=True, description="Require the input."),
            Control("disabled", "boolean", default=False, description="Disable the field and input."),
            Control("readonly", "boolean", default=False, description="Make the input read-only."),
            Control(
                "invalid",
                "boolean",
                default=False,
                description="Show invalid semantics and an error.",
            ),
            Control(
                "orientation",
                "select",
                "vertical",
                "Field layout direction.",
                ("vertical", "horizontal"),
            ),
            Control("density", "select", "comfortable", "Field spacing.", ("comfortable", "compact")),
        ),
        renderer=_render_field,
    ),
    StorybookScenario(
        id="table/static",
        title="Static",
        group="Table",
        description="Semantic table states with a nested Button.",
        usage="""from citry_ui import CTable, CTableColumn, CTableRow

table = CTable(
    columns=(CTableColumn("name", "Project", row_header=True),),
    rows=(CTableRow("citry", {"name": "Citry"}),),
    slots={"caption": "Projects"},
)""",
        controls=(
            Control("state", "select", "ready", "Server-rendered table state.", ("ready", "loading", "error")),
            Control("density", "select", "comfortable", "Cell spacing.", ("comfortable", "compact")),
            Control("striped", "boolean", default=True, description="Stripe alternating rows."),
            Control("hover", "boolean", default=True, description="Highlight the hovered row."),
            Control(
                "sticky_header",
                "boolean",
                default=False,
                description="Keep the header at the scroll boundary.",
            ),
        ),
        renderer=_render_table,
    ),
    StorybookScenario(
        id="tabs/server-selected",
        title="Interactive",
        group="Tabs",
        description="Server-rendered ARIA relationships with pointer and keyboard selection.",
        usage=(
            "from citry import Component\n\n"
            "class AccountTabs(Component):\n"
            '    template = """\n'
            '      <c-CTabs default_value="account" aria_label="Account settings">\n'
            "        {# CTab and CTabPanel declarations #}\n"
            "      </c-CTabs>\n"
            '    """'
        ),
        controls=(
            Control("selected", "select", "account", "Server-selected tab.", ("account", "security")),
            Control(
                "orientation",
                "select",
                "horizontal",
                "Tab-list orientation and keyboard axis.",
                ("horizontal", "vertical"),
            ),
            Control("direction", "select", "ltr", "Writing direction metadata.", ("ltr", "rtl")),
            Control(
                "activation",
                "select",
                "automatic",
                "Whether focus selects or Enter and Space activate.",
                ("automatic", "manual"),
            ),
        ),
        renderer=_render_tabs,
        client_interactive=True,
        ready_selector="[data-citry-tabs-root][data-citry-tabs-initialized]",
    ),
    StorybookScenario(
        id="readiness/reactive-state",
        title="Reactive state",
        group="Readiness",
        description=("Contributor-only pressure probe for client state, fragment assets, replacement, and cleanup."),
        usage=(
            "# Contributor-only readiness probe. Production component specifications\n"
            "# are authored separately before they enter the public Citry UI catalog."
        ),
        controls=(
            Control(
                "generation",
                "select",
                "first",
                "Replacement generation used by the lifecycle audit.",
                ("first", "second", "delayed", "never", "slow"),
            ),
        ),
        renderer=_render_reactive_probe,
        client_interactive=True,
        ready_selector='.citry-ui-readiness-probe[data-ready="true"]',
        ready_timeout_ms=1_500,
    ),
)

SCENARIOS_BY_ID = {scenario.id: scenario for scenario in SCENARIOS}
if len(SCENARIOS_BY_ID) != len(SCENARIOS):
    raise ValueError("Storybook scenario IDs must be unique.")


__all__ = [
    "CATALOG_SCHEMA_VERSION",
    "SCENARIOS",
    "SCENARIOS_BY_ID",
    "Control",
    "ScenarioArgsError",
    "StorybookScenario",
]
