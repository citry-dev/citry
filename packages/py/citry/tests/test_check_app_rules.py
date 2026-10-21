"""
Tests for the ``citry check`` rules that need the loaded application.

Each rule reads a fact a template alone does not show: whether a page uses
Vue, a component's own props, a server event's data class, or the keys a
component's ``css_data()`` returns. The templates of the error benchmark's
mistakes (``benchmarks/errors/cases``) must be reported, and realistic
neighbors must stay silent.
"""

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

import pytest

from citry import Citry, Component, LintSettings
from citry._app_selection import CheckAppSelection
from citry._checker import check_project

try:
    import pydantic
except ImportError:
    pydantic = None  # type: ignore[assignment]

# The value the m41 benchmark sends to the browser from a module constant.
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
    # The benchmark's board page has js_data() and JavaScript.
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
    # The m28 benchmark's status line closes itself instead of emitting.
    engine = _prop_engine('<p class="status"><button type="button" @click="open = false">Close</button></p>')

    assert _findings(engine, tmp_path, _PROP) == [
        (
            _PROP,
            "error",
            "Prop 'open' is read-only, so this assignment does not change it. Emit an event to let the"
            " parent change it.",
        ),
        # The method's `this.open = false` is a warning: the check reads text.
        (
            _PROP,
            "warning",
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
    "template",
    [
        # Reading, comparing, and emitting are fine.
        '<button @click="$emit(\'close\')" :disabled="open == false"></button>',
        "<p v-text=\"open ? 'open' : 'closed'\"></p>",
        # A field of an object prop may change, and data is the component's own.
        '<button @click="open.count = 1; local = 2"></button>',
        # A loop variable with the prop's name is not the prop.
        '<li v-for="open in items" @click="open = 1"></li>',
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
        # The benchmark's m18, m32, and m33 buttons.
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

    assert (
        _findings(_counter_engine('<button @c-click="save({amont: 1})">x</button>', data_class=model), tmp_path) == []
    )


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
    # The m43 benchmark reads --acent for the accent key.
    engine = _css_engine("h1 {\n  color: var(--acent);\n}\n", keys={"accent": "blue"})

    assert _findings(engine, tmp_path, _CSS) == [
        (_CSS, "warning", "Nothing sets --acent, so this var() has no value. Did you mean --accent, from css_data()?"),
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
    assert "API_BASE is a PurePosixPath" in findings[0].message


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
        f"{package / 'card.py'}:5: Citry cannot tell from this file that Card is a component, because its base class"
        " BaseCard comes from another module, so this template is checked only by citry check with your application"
        " loaded. [citry.check.template-not-checked]",
    )
    assert report.exit_code == 0
