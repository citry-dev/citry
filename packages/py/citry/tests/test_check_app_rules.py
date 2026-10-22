"""
Tests for the ``citry check`` rules that need the loaded application.

Each rule reads a fact a template alone does not show: whether a page uses
Vue, a component's own props, a server event's data class, or the keys a
component's ``css_data()`` returns. The templates of the error benchmark's
mistakes (``benchmarks/errors/cases``) must be reported, and realistic
neighbors must stay silent.
"""

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

import pytest

from citry import Citry, Component, LintSettings
from citry._app_selection import CheckAppSelection
from citry._checker import check_project
from citry._path_checks import PathLookup, register_path_checker
from citry._registry_lint import (
    annotation_from_type_display,
    root_relative_path,
    server_event_payload_from_description,
)
from citry.ext.events import event

try:
    import pydantic
except ImportError:
    pydantic = None  # type: ignore[assignment]

# The value the benchmark case m41-browser-value-not-json sends to the
# browser from a module constant.
API_BASE = PurePosixPath("/api")
PLAIN_API_BASE = "/api"


def _findings(engine: Citry, tmp_path, *codes: str) -> list[tuple[str, str, str]]:
    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    return [(item.code, item.severity, item.message) for item in report.findings if item.code in codes]


def _report(engine: Citry, tmp_path):
    return check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)


################################################
# A COMPONENT REPEATED WITHOUT #c-key
################################################

_KEY = "citry.browser.missing-component-key"
_CARD_LOOP = """
  <c-for each="project in projects">
    <c-Card
      c-title="project.title"
    />
  </c-for>
"""


def _browser_data(self, kwargs, slots):
    return {"hiddenTitles": []}


def _key_engine(*, owner: dict[str, object], card: dict[str, object], template: str = _CARD_LOOP) -> Citry:
    engine = Citry(autodiscover=False)
    type(
        "Card",
        (Component,),
        {"citry": engine, "template": "<article>{{ title }}</article>", "__module__": __name__, **card},
    )
    type("Board", (Component,), {"citry": engine, "template": template, "__module__": __name__, **owner})
    return engine


def test_a_repeated_component_without_a_key_is_reported_when_the_page_uses_vue(tmp_path):
    # The board page of case m51-list-key-missing has js_data() and JavaScript.
    engine = _key_engine(
        owner={
            "js_data": _browser_data,
            "js": "$component({});",
        },
        card={},
    )

    assert _findings(engine, tmp_path, _KEY) == [
        (
            _KEY,
            "error",
            "<c-Card> repeats inside <c-for> but has no #c-key. This page uses Vue, and the render fails when the"
            " loop has two items.",
        ),
    ]


@pytest.mark.parametrize(
    ("owner", "card"),
    [
        # Either side's JavaScript, browser data, Events class, or Vue
        # attribute makes the page use Vue.
        ({}, {"js": "$component({});"}),
        ({}, {"js_data": _browser_data}),
        ({}, {"Events": type("Events", (), {})}),
        ({}, {"template": '<article v-if="true">{{ title }}</article>'}),
        ({"Events": type("Events", (), {})}, {}),
        ({"template": '<div @click="1"></div>' + _CARD_LOOP}, {}),
    ],
)
def test_each_way_a_page_uses_vue_reports_the_repeated_component(tmp_path, owner, card):
    assert [code for code, _severity, _message in _findings(_key_engine(owner=owner, card=card), tmp_path, _KEY)] == [
        _KEY
    ]


@pytest.mark.parametrize(
    ("owner", "card", "template"),
    [
        # A server-only page renders a loop without keys.
        ({}, {}, _CARD_LOOP),
        # State alone does not make the page use Vue.
        ({}, {"State": type("State", (), {"__annotations__": {"n": int}, "n": 0})}, _CARD_LOOP),
        # These render into the caller's HTML, so the loop needs no key.
        ({"js": "$component({});"}, {"transparent": True}, _CARD_LOOP),
        ({"js": "$component({});"}, {"simple": True}, _CARD_LOOP),
        # A key, a call outside the loop, and the c-empty body are fine.
        (
            {"js": "$component({});"},
            {},
            '<c-for each="project in projects"><c-Card #c-key="project.slug" c-title="project.title" /></c-for>',
        ),
        ({"js": "$component({});"}, {}, "<c-Card c-title=\"'one'\" />"),
        (
            {"js": "$component({});"},
            {},
            '<c-for each="project in projects"><p>{{ project }}</p></c-for><c-empty><c-Card c-title="\'none\'" />'
            "</c-empty>",
        ),
    ],
)
def test_a_repeated_component_that_renders_fine_is_not_reported(tmp_path, owner, card, template):
    assert _findings(_key_engine(owner=owner, card=card, template=template), tmp_path, _KEY) == []


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        # A keyed component tells each repetition of its body apart, so the
        # calls inside it need no key of their own.
        ('<c-for each="p in projects"><c-Card #c-key="p.slug"><c-Card /></c-Card></c-for>', []),
        ('<c-Card c-for="p in projects" #c-key="p.slug"><c-Card /></c-Card>', []),
        # A key on a plain element does not do that.
        ('<div c-for="p in projects" #c-key="p.slug"><c-Card /></div>', ["c-Card"]),
        # The <c-empty> of an inner loop repeats with the outer loop.
        (
            '<c-for each="p in projects"><c-for each="t in p.tasks"><i>t</i></c-for>'
            "<c-empty><c-Card /></c-empty></c-for>",
            ["c-Card"],
        ),
    ],
)
def test_keys_on_wrappers_and_inner_empty_bodies_follow_the_runtime(tmp_path, template, expected):
    engine = _key_engine(owner={"js": "$component({});"}, card={}, template=template)

    assert [
        message.split(">", 1)[0][1:] for _code, _severity, message in _findings(engine, tmp_path, _KEY)
    ] == expected


_EMPTY_DATA_ENGINE = Citry(autodiscover=False)


class EmptyDataCard(Component):
    citry = _EMPTY_DATA_ENGINE
    template = "<i>card</i>"


class EmptyDataBoard(Component):
    citry = _EMPTY_DATA_ENGINE
    template = '<c-for each="p in projects"><c-EmptyDataCard /></c-for>'

    def js_data(self, kwargs, slots):
        # The page uses Vue only when the data is not empty.
        return {}


def test_a_js_data_that_always_returns_nothing_does_not_make_the_page_use_vue(tmp_path):
    assert _findings(_EMPTY_DATA_ENGINE, tmp_path, _KEY) == []


def test_the_missing_key_rule_follows_the_component_lint_class(tmp_path):
    lint = type("Lint", (), {"rule_missing_component_key": "warning"})
    engine = _key_engine(owner={"js": "$component({});", "Lint": lint}, card={})

    assert [severity for _code, severity, _message in _findings(engine, tmp_path, _KEY)] == ["warning"]


################################################
# A COMPONENT THAT ASSIGNS TO ITS OWN PROP
################################################

_PROP = "citry.browser.prop-assignment"
_STATUS_JS = """
  $component({
    props: {
      open: { type: Boolean, required: true },
    },
    data() {
      return { local: 1 };
    },
    emits: ['close'],
    methods: {
      close() {
        this.open = false;
        this.local = 2;
      },
    },
  });
"""


def _prop_engine(template: str, *, js: str = _STATUS_JS, lint: LintSettings | None = None) -> Citry:
    engine = Citry(autodiscover=False, **({"lint": lint} if lint is not None else {}))
    type("Status", (Component,), {"citry": engine, "template": template, "js": js, "__module__": __name__})
    return engine


def test_a_template_assignment_to_an_own_prop_is_reported(tmp_path):
    # The status line of case m28-input-written-by-child closes itself
    # instead of emitting an event.
    engine = _prop_engine('<p class="status"><button type="button" @click="open = false">Close</button></p>')

    assert _findings(engine, tmp_path, _PROP) == [
        (
            _PROP,
            "error",
            "Prop 'open' is read-only, so this assignment does not change it. Emit an event to let the"
            " parent change it.",
        ),
        # The method's `this.open = false` follows the rule's severity too,
        # because the parser marks the member as written.
        (
            _PROP,
            "error",
            "Prop 'open' is read-only, so this assignment does not change it. Emit an event to let the"
            " parent change it.",
        ),
    ]


@pytest.mark.parametrize(
    "expression",
    ["open += 1", "open++", "--open", "(e) => { open ||= e }"],
)
def test_every_assignment_operator_counts(tmp_path, expression):
    engine = _prop_engine(f'<button @click="{expression}"></button>', js=_STATUS_JS.replace("this.open = false;", ""))

    assert [severity for _code, severity, _message in _findings(engine, tmp_path, _PROP)] == ["error"]


def test_v_model_on_an_own_prop_is_reported(tmp_path):
    engine = _prop_engine('<input type="checkbox" v-model="open">', js=_STATUS_JS.replace("this.open = false;", ""))

    assert _findings(engine, tmp_path, _PROP) == [
        (
            _PROP,
            "error",
            "v-model writes to prop 'open', which is read-only, so the input cannot change it. Emit an event to let"
            " the parent change it.",
        ),
    ]


@pytest.mark.parametrize(
    "expression",
    [
        # A comment between the name and `=` hides the write from a text scan.
        "open /* close */ = false",
        # Destructuring writes each target name.
        "[open] = [false]",
    ],
)
def test_writes_the_parser_sees_are_reported(tmp_path, expression):
    engine = _prop_engine(f'<button @click="{expression}"></button>', js=_STATUS_JS.replace("this.open = false;", ""))

    assert [severity for _code, severity, _message in _findings(engine, tmp_path, _PROP)] == ["error"]


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        ("this.open = false;", ["error"]),
        ("this.open++;", ["error"]),
        ("[this.open] = [false];", ["error"]),
        # A field of the prop may change, and comparing only reads it.
        ("this.open.count = 1;", []),
        ("if (this.open == false) this.local = 2;", []),
    ],
)
def test_component_javascript_writes_follow_the_rule_severity(tmp_path, method, expected):
    engine = _prop_engine("<p>status</p>", js=_STATUS_JS.replace("this.open = false;", method))

    assert [severity for _code, severity, _message in _findings(engine, tmp_path, _PROP)] == expected


def test_component_javascript_writes_use_a_warning_severity_when_set(tmp_path):
    engine = _prop_engine("<p>status</p>", lint=LintSettings(rule_prop_assignment="warning"))

    assert [severity for _code, severity, _message in _findings(engine, tmp_path, _PROP)] == ["warning"]


@pytest.mark.parametrize(
    "template",
    [
        # Reading, comparing, and emitting are fine.
        '<button @click="$emit(\'close\')" :disabled="open == false"></button>',
        "<p v-text=\"open ? 'open' : 'closed'\"></p>",
        # A field of an object prop may change, and data is the component's own.
        '<button @click="open.count = 1; local = 2"></button>',
        # A loop variable with the prop's name is not the prop.
        '<li v-for="open in items" @click="open = 1"></li>',
        # `--` on the next line updates `count`, not the `open` before it.
        '<button @click="open\n--count"></button>',
    ],
)
def test_reads_and_other_names_are_not_reported(tmp_path, template):
    engine = _prop_engine(template, js=_STATUS_JS.replace("this.open = false;", ""))

    assert _findings(engine, tmp_path, _PROP) == []


def test_a_component_without_javascript_declares_no_props(tmp_path):
    engine = Citry(autodiscover=False)
    type("Status", (Component,), {"citry": engine, "template": '<button @click="open = false"></button>'})

    assert _findings(engine, tmp_path, _PROP) == []


def test_the_prop_assignment_rule_follows_the_settings(tmp_path):
    engine = _prop_engine('<button @click="open = false"></button>', lint=LintSettings(rule_prop_assignment="ignore"))

    assert _findings(engine, tmp_path, _PROP) == []


################################################
# SERVER EVENT ARGUMENTS
################################################

_UNKNOWN = "citry.browser.unknown-server-event-field"
_MISSING = "citry.browser.missing-server-event-field"
_INCOMPATIBLE = "citry.browser.incompatible-server-event-field"
_PAYLOAD = (_UNKNOWN, _MISSING, _INCOMPATIBLE)


class SaveIn:
    amount: int


class SearchIn:
    query: str
    page: int = 1
    order: Literal["asc", "desc"] = "asc"


@dataclass
class NoteIn:
    text: str
    pinned: bool = False


def _save_without_data(self):
    return None


def _save_handler(data_class: type):
    # The annotation is read when the handler is defined, so each data class
    # gets its own function.
    def save(self, data: data_class):  # type: ignore[valid-type]
        return None

    return save


def _counter_engine(button: str, *, data_class: type | None = SaveIn) -> Citry:
    engine = Citry(autodiscover=False)
    save = _save_without_data if data_class is None else _save_handler(data_class)
    type(
        "Counter",
        (Component,),
        {
            "citry": engine,
            "Events": type("Events", (), {"save": save}),
            "template": f'<section class="counter">{button}</section>',
            "__module__": __name__,
        },
    )
    return engine


@pytest.mark.parametrize(
    ("button", "expected"),
    [
        # The buttons of cases m18-payload-field, m32-payload-type, and
        # m33-payload-missing-field.
        (
            '<button type="button" @c-click="save({amont: 1})">Add</button>',
            [
                (
                    _MISSING,
                    "Server event 'save' requires field 'amount', which this call does not send, so the server"
                    " rejects it.",
                ),
                (
                    _UNKNOWN,
                    "Server event 'save' has no field 'amont', so the server rejects this call. Did you mean"
                    " 'amount'?",
                ),
            ],
        ),
        (
            '<button type="button" @c-click="save({amount: \'1\'})">Add</button>',
            [(_INCOMPATIBLE, "Server event 'save' rejects this value for field 'amount': Expected int, got str.")],
        ),
        (
            '<button type="button" @c-click="save()">Add</button>',
            [
                (
                    _MISSING,
                    "Server event 'save' requires field 'amount', which this call does not send, so the server"
                    " rejects it.",
                )
            ],
        ),
    ],
)
def test_the_benchmark_payload_mistakes_are_reported(tmp_path, button, expected):
    findings = _findings(_counter_engine(button), tmp_path, *_PAYLOAD)

    assert [(code, message) for code, _severity, message in findings] == expected
    assert {severity for _code, severity, _message in findings} == {"error"}


@pytest.mark.parametrize(
    "button",
    [
        '<button @c-click="save({amount: 1})">Add</button>',
        # JSON sends 2.0 as 2, which an int field takes.
        '<button @c-click="save({amount: 2.0})">Add</button>',
        # A value Citry cannot read is left to the server.
        '<button @c-click="save({amount: count})">Add</button>',
        # A spread may add the missing field.
        '<button @c-click="save({...defaults})">Add</button>',
        # A form sends its fields when the binding has no arguments.
        '<form @c-submit.prevent="save"><input name="amount" type="number"></form>',
        '<form @c-submit.prevent="save()"><input name="amount" type="number"></form>',
        '<div @c-submit="save"><form><input name="amount"></form></div>',
    ],
)
def test_payloads_the_server_accepts_or_cannot_be_read_are_not_reported(tmp_path, button):
    assert _findings(_counter_engine(button), tmp_path, *_PAYLOAD) == []


def test_a_key_next_to_a_spread_is_still_checked(tmp_path):
    findings = _findings(
        _counter_engine('<button @c-click="save({...base, amont: 1})">x</button>'), tmp_path, *_PAYLOAD
    )

    assert [code for code, _severity, _message in findings] == [_UNKNOWN]


def test_a_handler_without_data_rejects_every_key(tmp_path):
    findings = _findings(
        _counter_engine('<button @c-click="save({amount: 1})">x</button>', data_class=None), tmp_path, *_PAYLOAD
    )

    assert findings == [
        (
            _UNKNOWN,
            "error",
            "Server event 'save' takes no data, so the server rejects this call because of field 'amount'.",
        ),
    ]


@pytest.mark.parametrize(
    ("button", "expected"),
    [
        ("<button @c-click=\"save({query: 'x', order: 'up'})\">x</button>", [_INCOMPATIBLE]),
        ("<button @c-click=\"save({query: 'x', order: 'desc', page: 2})\">x</button>", []),
        # Both results of a condition are checked.
        ("<button @c-click=\"save({query: 'x', page: wide ? 2 : 'all'})\">x</button>", [_INCOMPATIBLE]),
        ('<button @c-click="save({page: 2})">x</button>', [_MISSING]),
    ],
)
def test_defaults_literals_and_conditions_follow_the_data_class(tmp_path, button, expected):
    findings = _findings(_counter_engine(button, data_class=SearchIn), tmp_path, *_PAYLOAD)

    assert [code for code, _severity, _message in findings] == expected


def _get_engine(button: str) -> Citry:
    engine = Citry(autodiscover=False)

    @event(methods=("GET",))
    def save(self, data: SearchIn):
        return None

    type(
        "Search",
        (Component,),
        {"citry": engine, "Events": type("Events", (), {"save": save}), "template": button, "__module__": __name__},
    )
    return engine


@pytest.mark.parametrize(
    ("button", "expected"),
    [
        # A GET query string carries text, which the server binds to an
        # int field, so '2' and 1 for a str field both work there.
        ("<button @c-click=\"save({query: 'x', page: '2'})\">x</button>", []),
        ('<button @c-click="save({query: 1})">x</button>', []),
        # Text that is no number fails both ways.
        ("<button @c-click=\"save({query: 'x', page: 'two'})\">x</button>", [_INCOMPATIBLE]),
    ],
)
def test_a_get_handler_accepts_what_its_query_string_binds(tmp_path, button, expected):
    findings = _findings(_get_engine(button), tmp_path, *_PAYLOAD)

    assert [code for code, _severity, _message in findings] == expected


def test_only_the_last_of_two_equal_keys_is_sent(tmp_path):
    engine = _counter_engine("<button @c-click=\"save({amount: 'x', amount: 1})\">x</button>")

    assert _findings(engine, tmp_path, *_PAYLOAD) == []


def test_a_dataclass_data_class_is_checked_too(tmp_path):
    findings = _findings(
        _counter_engine("<button @c-click=\"save({text: 'x', pinned: 'yes'})\">x</button>", data_class=NoteIn),
        tmp_path,
        *_PAYLOAD,
    )

    assert [code for code, _severity, _message in findings] == [_INCOMPATIBLE]


@pytest.mark.skipif(pydantic is None, reason="pydantic is not installed")
def test_a_pydantic_data_class_is_not_checked(tmp_path):
    model = type("SaveModel", (pydantic.BaseModel,), {"__annotations__": {"amount": int}, "__module__": __name__})

    engine = _counter_engine('<button @c-click="save({amont: 1})">x</button>', data_class=model)

    assert _findings(engine, tmp_path, *_PAYLOAD) == []


def test_a_template_shared_with_another_data_class_is_not_checked(tmp_path):
    engine = _counter_engine('<button @c-click="save({amont: 1})">x</button>')
    counter = engine.get("counter")

    def save(self, data: SearchIn):
        return None

    # A subclass renders the same template with another data class, so the
    # binding cannot be checked against one class.
    type("OtherCounter", (counter,), {"Events": type("Events", (), {"save": save}), "__module__": __name__})

    assert _findings(engine, tmp_path, *_PAYLOAD) == []


def test_each_payload_rule_has_its_own_setting(tmp_path):
    lint = LintSettings(rule_unknown_server_event_field="warning", rule_missing_server_event_field="ignore")
    engine = Citry(autodiscover=False, lint=lint)

    def save(self, data: SaveIn):
        return None

    type(
        "Counter",
        (Component,),
        {
            "citry": engine,
            "Events": type("Events", (), {"save": save}),
            "template": '<button @c-click="save({amont: 1})">x</button>',
            "__module__": __name__,
        },
    )

    assert [(code, severity) for code, severity, _message in _findings(engine, tmp_path, *_PAYLOAD)] == [
        (_UNKNOWN, "warning"),
    ]


################################################
# THE EDITOR'S COPY OF WHAT A HANDLER ACCEPTS
################################################


def _description(**overrides: object) -> dict[str, object]:
    description: dict[str, object] = {
        "name": "save",
        "methods": ["POST"],
        "request_schema": {
            "kind": "fields",
            "import_path": "app.SaveIn",
            "fields": [
                {"name": "amount", "required": True, "type_display": "int", "type_fidelity": "normalized"},
                {"name": "when", "required": False, "type_display": "datetime.date", "type_fidelity": "normalized"},
            ],
        },
        "extra_fields": "reject",
        "validated_by": "citry",
    }
    description.update(overrides)
    return description


def test_a_handler_description_gives_the_same_payload_rules_as_the_data_class():
    payload = server_event_payload_from_description(_description())

    assert payload is not None
    assert payload.takes_data
    assert payload.rejects_unknown
    assert not payload.query_string
    assert {name: field.required for name, field in (payload.fields or {}).items()} == {"amount": True, "when": False}
    # Only a type the text proves is checked; a class name is left alone.
    assert (payload.fields or {})["amount"].annotation is int
    assert (payload.fields or {})["when"].annotation is None


@pytest.mark.parametrize(
    "overrides",
    [
        # An older Citry sends neither key, so nothing proves Citry checks the values.
        {"extra_fields": None, "validated_by": None},
        {"validated_by": "pydantic"},
        {"validated_by": "something-new"},
        {"extra_fields": "something-new"},
        {"request_schema": {"kind": "fields", "import_path": None, "fields": [{"name": 1, "required": True}]}},
    ],
)
def test_a_handler_description_that_proves_nothing_turns_the_rules_off(overrides):
    description = {key: value for key, value in _description(**overrides).items() if value is not None}

    assert server_event_payload_from_description(description) is None


def test_a_handler_description_reads_the_editor_copy_and_other_shapes():
    # The editor's frozen copy holds tuples where the JSON had lists.
    frozen = _description(methods=("GET", "POST"))
    frozen["request_schema"] = {**frozen["request_schema"], "fields": tuple(frozen["request_schema"]["fields"])}
    payload = server_event_payload_from_description(frozen)
    assert payload is not None
    assert payload.query_string
    assert set(payload.fields or {}) == {"amount", "when"}

    no_data = server_event_payload_from_description(_description(request_schema=None))
    assert no_data is not None
    assert not no_data.takes_data

    # An opaque schema names no fields, so only a handler-level fact is known.
    opaque = server_event_payload_from_description(
        _description(request_schema={"kind": "opaque", "import_path": None, "fields": []})
    )
    assert opaque is not None
    assert opaque.fields is None


@pytest.mark.parametrize(
    ("text", "annotation"),
    [
        ("int", int),
        ("str | None", str | None),
        ('Literal["asc", "desc"]', Literal["asc", "desc"]),
        ("Literal[1, -2]", Literal[1, -2]),
        ("list[int]", list[int]),
        ("tuple[int, ...]", tuple[int, ...]),
        ("dict[str, float]", dict[str, float]),
        ("Optional[bool]", bool | None),
        ("datetime.date", None),
        ("list[app.Item]", None),
        ("Literal[Color.RED]", None),
        ("not a type (", None),
    ],
)
def test_type_display_text_becomes_an_annotation_only_when_the_text_proves_it(text, annotation):
    assert annotation_from_type_display(text) == annotation


################################################
# FORM FIELDS SENT TO A SERVER EVENT
################################################

_UNKNOWN_FORM = "citry.browser.unknown-form-field"
_MISSING_FORM = "citry.browser.missing-form-field"
_FORM = (_UNKNOWN_FORM, _MISSING_FORM)


class QueryIn:
    q: str


def test_the_benchmark_form_field_mistake_is_reported(tmp_path):
    # The search form of case m44-form-field-name, with the control's name
    # misspelled.
    form = """
        <form role="search" @c-submit.prevent="save">
          <input
            type="search"
            name="qeury"
            v-model="query"
          />
          <button type="submit">Search</button>
        </form>
    """
    findings = _findings(_counter_engine(form, data_class=QueryIn), tmp_path, *_FORM)

    assert findings == [
        (
            _MISSING_FORM,
            "error",
            "Server event 'save' requires field 'q', but no control in this form has that name, so the server"
            " rejects every submit.",
        ),
        (
            _UNKNOWN_FORM,
            "error",
            "The form sends field 'qeury', which server event 'save' does not declare, so the server rejects the"
            " submit.",
        ),
    ]


@pytest.mark.parametrize(
    ("form", "data_class", "expected"),
    [
        # A name one slip from a declared field gets a suggestion.
        (
            '<form @c-submit.prevent="save"><input name="query"><input name="paeg"></form>',
            SearchIn,
            [
                (
                    _UNKNOWN_FORM,
                    "The form sends field 'paeg', which server event 'save' does not declare, so the server rejects"
                    " the submit. Did you mean 'page'?",
                )
            ],
        ),
        # A handler without data rejects every field.
        (
            '<form @c-submit.prevent="save()"><input name="q"></form>',
            None,
            [
                (
                    _UNKNOWN_FORM,
                    "The form sends field 'q', but server event 'save' takes no data, so the server rejects the"
                    " submit.",
                )
            ],
        ),
        # A <textarea> and a <select> send their names too.
        (
            '<form @c-submit.prevent="save"><select name="q"><option>a</option></select>'
            '<textarea name="nots"></textarea></form>',
            QueryIn,
            [
                (
                    _UNKNOWN_FORM,
                    "The form sends field 'nots', which server event 'save' does not declare, so the server rejects"
                    " the submit.",
                )
            ],
        ),
        # The button that submits the form sends its name too.
        (
            '<form @c-submit.prevent="save"><input name="q"><button name="action" value="go">Go</button></form>',
            QueryIn,
            [
                (
                    _UNKNOWN_FORM,
                    "The form sends field 'action', which server event 'save' does not declare, so the server"
                    " rejects the submit.",
                )
            ],
        ),
        # An image button sends where it was clicked, never its bare name.
        (
            '<form @c-submit.prevent="save"><input name="q"><input type="image" name="go" src="go.svg" alt="Go">'
            "</form>",
            QueryIn,
            [
                (
                    _UNKNOWN_FORM,
                    "The form sends field 'go.x', which server event 'save' does not declare, so the server"
                    " rejects the submit.",
                ),
                (
                    _UNKNOWN_FORM,
                    "The form sends field 'go.y', which server event 'save' does not declare, so the server"
                    " rejects the submit.",
                ),
            ],
        ),
        # A form that shows every control it sends, without the required one.
        (
            '<form @c-submit.prevent="save"><button>Go</button></form>',
            QueryIn,
            [
                (
                    _MISSING_FORM,
                    "Server event 'save' requires field 'q', but no control in this form has that name, so the"
                    " server rejects every submit.",
                )
            ],
        ),
    ],
)
def test_form_fields_the_server_rejects_are_reported(tmp_path, form, data_class, expected):
    findings = _findings(_counter_engine(form, data_class=data_class), tmp_path, *_FORM)

    assert [(code, message) for code, _severity, message in findings] == expected


@pytest.mark.parametrize(
    "form",
    [
        '<form @c-submit.prevent="save"><input name="q"></form>',
        # The server removes Django's CSRF field before it checks the class.
        '<form @c-submit.prevent="save"><input name="q"><input type="hidden" name="csrfmiddlewaretoken"></form>',
        # Controls the browser does not send with this form.
        '<form @c-submit.prevent="save"><input name="q"><input name="extra" disabled></form>',
        '<form @c-submit.prevent="save"><input name="q"><input name="extra" :disabled="busy"></form>',
        '<form @c-submit.prevent="save"><input name="q"><input name="other" form="elsewhere"></form>',
        '<form @c-submit.prevent="save"><input name="q"><input type="file" name="upload"></form>',
        '<form @c-submit.prevent="save"><input name="q"><button type="button" name="go">Go</button></form>',
        # A button whose click is prevented never submits.
        '<form @c-submit.prevent="save"><input name="q"><button name="add" @click.prevent="addRow">+</button></form>',
        # Vue's `^name` and `.name` shorthands bind the name as an expression.
        '<form @c-submit.prevent="save"><input ^name="field"></form>',
        '<form @c-submit.prevent="save"><input name="q"><button ^type="kind" name="go">Go</button></form>',
        '<form @c-submit.prevent="save"><fieldset disabled><input name="x"></fieldset><input name="q"></form>',
        '<form @c-submit.prevent="save"><input name="x" v-bind="attrs"><input name="q"></form>',
        # A required field may come from a control the template cannot see.
        '<form id="search" @c-submit.prevent="save"><button>Go</button></form>',
        '<form @c-submit.prevent="save"><c-SearchField /></form>',
        '<form @c-submit.prevent="save"><input :name="field"></form>',
        '<form @c-submit.prevent="save"><input :name.prop="field"></form>',
        # A library may add controls inside content Citry leaves alone.
        '<form @c-submit.prevent="save"><div #c-ignore></div><button>Go</button></form>',
        '<form @c-submit.prevent="save"><search-box></search-box></form>',
        '<form @c-submit.prevent="save"><input v-for="name in names" :name="name"></form>',
        '<form @c-submit.prevent="save"><slot></slot></form>',
        # A required field inside a condition still has its control.
        '<form @c-submit.prevent="save"><c-if cond="ready"><input name="q"></c-if></form>',
        # Arguments written in the binding replace the form's fields.
        '<form @c-submit.prevent="save({q: \'x\'})"><input name="zzz"></form>',
        # A submit from inside another element is not read as this form's.
        '<div @c-submit="save"><form><input name="zzz"></form></div>',
    ],
)
def test_form_fields_the_server_accepts_or_cannot_be_read_are_not_reported(tmp_path, form):
    assert _findings(_counter_engine(form, data_class=QueryIn), tmp_path, *_FORM) == []


def test_the_csrf_field_names_setting_is_followed(tmp_path):
    form = '<form @c-submit.prevent="save"><input name="q"><input type="hidden" name="authenticity_token"></form>'
    engine = Citry(autodiscover=False, extensions_defaults={"events": {"_csrf_field_names": ["authenticity_token"]}})

    def save(self, data: QueryIn):
        return None

    type(
        "Search",
        (Component,),
        {"citry": engine, "Events": type("Events", (), {"save": save}), "template": form, "__module__": __name__},
    )

    assert _findings(engine, tmp_path, *_FORM) == []
    # Without the setting, the same field is unknown to the data class.
    assert [
        code for code, _severity, _message in _findings(_counter_engine(form, data_class=QueryIn), tmp_path, *_FORM)
    ] == [_UNKNOWN_FORM]


@pytest.mark.skipif(pydantic is None, reason="pydantic is not installed")
def test_a_form_for_a_pydantic_data_class_is_not_checked(tmp_path):
    model = type("QueryModel", (pydantic.BaseModel,), {"__annotations__": {"q": str}, "__module__": __name__})

    engine = _counter_engine('<form @c-submit.prevent="save"><input name="qeury"></form>', data_class=model)

    assert _findings(engine, tmp_path, *_FORM) == []


def test_each_form_rule_has_its_own_setting(tmp_path):
    lint = LintSettings(rule_unknown_form_field="warning", rule_missing_form_field="ignore")
    engine = Citry(autodiscover=False, lint=lint)

    def save(self, data: QueryIn):
        return None

    type(
        "Search",
        (Component,),
        {
            "citry": engine,
            "Events": type("Events", (), {"save": save}),
            "template": '<form @c-submit.prevent="save"><input name="qeury"></form>',
            "__module__": __name__,
        },
    )

    assert [(code, severity) for code, severity, _message in _findings(engine, tmp_path, *_FORM)] == [
        (_UNKNOWN_FORM, "warning"),
    ]


################################################
# A MISSPELLED css_data() VARIABLE
################################################

_CSS = "citry.css.misspelled-variable"


def _css_data_returning(keys: dict[str, str]):
    def css_data(self, kwargs, slots):
        return dict(keys)

    return css_data


def _css_engine(css: str, *, keys: dict[str, str] | None = None) -> Citry:
    engine = Citry(autodiscover=False)
    namespace: dict[str, object] = {"citry": engine, "template": "<h1>Board</h1>", "css": css, "__module__": __name__}
    if keys is not None:
        namespace["CssData"] = type("CssData", (), {"__annotations__": dict.fromkeys(keys, str)})
        namespace["css_data"] = _css_data_returning(keys)
    type("Board", (Component,), namespace)
    return engine


def test_a_var_one_slip_from_a_css_data_key_is_reported(tmp_path):
    # Case m43-css-variable-name reads --acent for the accent key.
    engine = _css_engine("h1 {\n  color: var(--acent);\n}\n", keys={"accent": "blue"})

    assert _findings(engine, tmp_path, _CSS) == [
        (
            _CSS,
            "warning",
            "Nothing sets --acent, so the browser ignores this declaration. Did you mean --accent, from css_data()?",
        ),
    ]


@pytest.mark.parametrize(
    "css",
    [
        "h1 { color: var(--accent); }",
        # A fallback still gives a value.
        "h1 { color: var(--acent, blue); }",
        # The CSS sets the property itself.
        ":root { --acent: blue; } h1 { color: var(--acent); }",
        # A site-wide variable that is not one slip from a key.
        "h1 { color: var(--brand-color); }",
        "/* var(--acent) */ h1 { color: red; }",
    ],
)
def test_other_custom_properties_are_not_reported(tmp_path, css):
    assert _findings(_css_engine(css, keys={"accent": "blue"}), tmp_path, _CSS) == []


def test_a_component_without_known_css_data_keys_is_not_checked(tmp_path):
    assert _findings(_css_engine("h1 { color: var(--acent); }"), tmp_path, _CSS) == []


################################################
# A js_data() VALUE FROM A MODULE CONSTANT
################################################

_JS_DATA = "citry.js-data.unsupported-type"


_JS_DATA_ENGINE = Citry(autodiscover=False)


class ApiPage(Component):
    citry = _JS_DATA_ENGINE
    template = "<p></p>"

    def js_data(self, kwargs, slots):
        return {"apiBase": API_BASE, "plain": PLAIN_API_BASE}


class ImportedApiPage(Component):
    citry = _JS_DATA_ENGINE
    template = "<p></p>"

    def js_data(self, kwargs, slots):
        # A name the method imports hides the module constant too.
        from string import ascii_letters as API_BASE  # noqa: N812

        return {"apiBase": API_BASE}


class CaughtApiPage(Component):
    citry = _JS_DATA_ENGINE
    template = "<p></p>"

    def js_data(self, kwargs, slots):
        # Names bound by `except ... as` and by a `match` capture hide the
        # module constant too.
        try:
            raise ValueError
        except ValueError as API_BASE:
            caught = str(API_BASE)
        match kwargs:
            case {"base": API_BASE}:
                pass
            case _:
                API_BASE = caught
        return {"apiBase": API_BASE}


class ShadowedApiPage(Component):
    citry = _JS_DATA_ENGINE
    template = "<p></p>"

    def js_data(self, kwargs, slots):
        API_BASE = "/api"
        return {"apiBase": API_BASE}


def test_a_module_constant_the_browser_cannot_receive_is_reported(tmp_path):
    findings = _report(_JS_DATA_ENGINE, tmp_path).findings

    # ApiPage's PLAIN_API_BASE is a string, and ShadowedApiPage's local
    # hides the module constant, so only ApiPage's apiBase is reported.
    assert [(item.code, item.severity, item.origin.rsplit(" ", 1)[-1]) for item in findings] == [
        (_JS_DATA, "warning", f"({__name__}.ApiPage.js_data)"),
    ]
    assert "API_BASE holds a value of type PurePosixPath" in findings[0].message


################################################
# A TEMPLATE --static CANNOT CHECK
################################################


def test_static_check_notes_a_template_whose_base_comes_from_the_project(tmp_path):
    package = tmp_path / "app"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "base.py").write_text(
        "from citry import Component\n\n\nclass BaseCard(Component):\n    pass\n", encoding="utf-8"
    )
    (package / "card.py").write_text(
        "from app.base import BaseCard\n"
        "from django_components import Component\n\n\n"
        "class Card(BaseCard):\n    template = '<article titel=\"x\">{{ title }}</article>'\n\n\n"
        "class Other(Component):\n    template = '<p>{% if x %}{% endif %}</p>'\n",
        encoding="utf-8",
    )

    report = check_project(CheckAppSelection(), tmp_path)

    # The template is skipped, so its misspelled attribute is not reported;
    # the note says so. A class from an installed package is not noted.
    assert report.findings == ()
    assert report.notes == (
        f"{package / 'card.py'}:5: Citry cannot tell from this file that Card is a component, because it extends"
        " BaseCard, which comes from another module, so this template is checked only when Citry loads your"
        " application and finds Card there. [citry.check.template-not-checked]",
    )
    assert report.exit_code == 0


################################################
# A LINK TO A PATH THE HOST APP DOES NOT SERVE
################################################

_URL = "citry.template.unknown-url"
# The paths the fake host serves: its pages, one route with a number, and
# its static files. The error benchmark's m45, m61 and m48 link to the
# misspelled or wrong neighbor of each.
_SERVED = frozenset({"/", "/about", "/static/avatar.svg"})


def _host_checker(asked: list[str] | None = None):
    def check(path: str) -> PathLookup:
        if asked is not None:
            asked.append(path)
        found = path in _SERVED or bool(re.fullmatch(r"/projects/\d+", path))
        return PathLookup(found, () if found else tuple(sorted(_SERVED)))

    return check


def _linked_engine(template: str, *, checker=None, lint: LintSettings | None = None, prefix: str | None = None):
    engine = Citry(autodiscover=False, lint=lint or LintSettings())
    if checker is not None:
        register_path_checker(engine, checker)
    if prefix is not None:
        engine.set_mounted_prefix(prefix)
    type("Page", (Component,), {"citry": engine, "template": template, "__module__": __name__})
    return engine


def test_links_to_paths_the_host_does_not_serve_are_reported(tmp_path):
    engine = _linked_engine(
        '<a href="/abuot">About</a>\n'
        '<a href="/projects/alpha">Project</a>\n'
        '<img src="/static/avtar.svg" alt="">\n'
        '<form action="/nowhere"></form>',
        checker=_host_checker(),
    )

    assert _findings(engine, tmp_path, _URL) == [
        (
            _URL,
            "warning",
            "Your app has no route or static file for '/abuot', so the browser gets a 404 Not Found. "
            "Did you mean '/about'?",
        ),
        (
            _URL,
            "warning",
            "Your app has no route or static file for '/projects/alpha', so the browser gets a 404 Not Found.",
        ),
        (
            _URL,
            "warning",
            "Your app has no route or static file for '/static/avtar.svg', so the browser gets a 404 Not Found. "
            "Did you mean '/static/avatar.svg'?",
        ),
        (_URL, "warning", "Your app has no route or static file for '/nowhere', so the browser gets a 404 Not Found."),
    ]


def test_links_the_host_does_not_decide_are_not_checked(tmp_path):
    asked: list[str] = []
    engine = _linked_engine(
        # Served paths, also with a query string, a fragment, a character
        # reference, or a percent escape; Citry's own routes under the
        # mounted prefix; and links the host app does not decide: another
        # site, a relative path, a fragment, a bound value, a component
        # input, and an attribute that is not a link.
        '<a href="/about?tab=1#team">About</a><a href=" /about ">About</a>'
        '<a href="/ab&#111;ut">About</a><a href="/%61bout">About</a>'
        '<script src="/citry/citry.js"></script>'
        '<a href="https://example.com/abuot">x</a><a href="//cdn.example.com/x.js">x</a>'
        '<a href="abuot">x</a><a href="#top">x</a><a href="mailto:a@b.c">x</a>'
        '<a :href="\'/abuot\'">x</a><a c-href="\'/abuot\'">x</a><a data-href="/abuot">x</a>'
        '<my-link href="/abuot"></my-link>'
        # The base folder and a server to connect to early are not pages.
        '<base href="/abuot/"><link rel="preconnect" href="/abuot">',
        checker=_host_checker(asked),
        prefix="/citry",
    )

    assert _findings(engine, tmp_path, _URL) == []
    # Each path is asked about once, and Citry's own routes not at all.
    assert asked == ["/about"]


def test_a_link_in_a_component_input_is_not_checked(tmp_path):
    engine = Citry(autodiscover=False)
    register_path_checker(engine, _host_checker())
    type(
        "Link",
        (Component,),
        {
            "citry": engine,
            "template": "<a>x</a>",
            "Kwargs": type("Kwargs", (), {"__annotations__": {"href": str}}),
            "__module__": __name__,
        },
    )
    type("Page", (Component,), {"citry": engine, "template": '<c-Link href="/abuot" />', "__module__": __name__})

    assert _findings(engine, tmp_path, _URL) == []


def test_links_are_noted_once_when_no_integration_registered_a_checker(tmp_path):
    engine = _linked_engine('<a href="/abuot">About</a><a href="/other">Other</a>')

    report = _report(engine, tmp_path)

    assert [item for item in report.findings if item.code == _URL] == []
    notes = [note for note in report.notes if "citry.check.url-checker-missing" in note]
    assert len(notes) == 1
    assert "Links such as '/abuot' were not checked" in notes[0]
    assert report.exit_code == 0


def test_no_note_when_the_rule_is_ignored(tmp_path):
    engine = _linked_engine('<a href="/abuot">About</a>', lint=LintSettings(rule_unknown_url="ignore"))

    assert not any("url-checker" in note for note in _report(engine, tmp_path).notes)


def test_a_failing_checker_skips_its_paths_with_one_note(tmp_path):
    def broken(path: str) -> PathLookup:
        if path == "/about":
            return PathLookup(found=True)
        raise RuntimeError("routes are not loaded")

    engine = _linked_engine('<a href="/abuot">x</a><a href="/zzz">x</a><a href="/about">x</a>', checker=broken)

    report = _report(engine, tmp_path)

    assert [item for item in report.findings if item.code == _URL] == []
    notes = [note for note in report.notes if "citry.check.url-checker-failed" in note]
    assert notes == [
        "Citry skipped 2 link paths, such as '/abuot', because asking your web framework whether your app "
        "serves them raised an error: RuntimeError: routes are not loaded [citry.check.url-checker-failed]"
    ]


def test_another_checker_can_serve_a_path_one_checker_misses(tmp_path):
    engine = _linked_engine('<a href="/blog">Blog</a>', checker=_host_checker())
    register_path_checker(engine, lambda path: PathLookup(path == "/blog"))

    assert _findings(engine, tmp_path, _URL) == []


def test_the_link_rule_follows_the_app_and_component_settings(tmp_path):
    engine = _linked_engine(
        '<a href="/abuot">About</a>', checker=_host_checker(), lint=LintSettings(rule_unknown_url="error")
    )
    type(
        "ProxiedPage",
        (Component,),
        {
            "citry": engine,
            "template": '<a href="/grafana">Dashboards</a>',
            # The proxy in front of the app serves this path.
            "Lint": type("Lint", (), {"rule_unknown_url": "ignore"}),
            "__module__": __name__,
        },
    )

    report = _report(engine, tmp_path)

    assert [(item.code, item.severity) for item in report.findings if item.code == _URL] == [(_URL, "error")]
    assert report.exit_code == 1


@pytest.mark.parametrize(
    ("written", "requested"),
    [
        ("/about", "/about"),
        (" /about?tab=1#team ", "/about"),
        ("\\about", "/about"),
        ("/static/../about", "/about"),
        ("/static/%2e%2e/about", "/about"),
        ("/a/./b/..", "/a/"),
        ("/..", "/"),
        # The browser resolves dots before it decodes an escaped slash, and
        # drops tabs and line breaks anywhere.
        ("/a%2Fb/..", "/"),
        ("/ab\tout", "/about"),
        ("/caf%C3%A9", "/café"),
        ("//cdn.example.com/x.js", None),
        ("\\\\cdn.example.com/x.js", None),
        ("https://example.com/", None),
        ("page.html", None),
        ("", None),
    ],
)
def test_a_link_is_checked_as_the_path_the_browser_requests(written, requested):
    assert root_relative_path(written) == requested
