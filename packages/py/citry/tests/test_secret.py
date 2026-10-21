"""
A `citry.Secret` stays on the server.

Citry refuses to send a Secret to the browser: rendering a component whose
`js_data()`, `css_data()`, or State holds one raises before any HTML leaves
the server, and `citry check` warns about it before the page runs. On the
server a Secret renders as `***` and can travel freely between components.

The benchmark case m42-secret-sent-to-browser (benchmarks/errors/cases)
returns a module constant `SECRET_TOKEN` from `js_data()`. Here it is
written as it would look once the project wraps the token in a Secret.
"""

from __future__ import annotations

import copy
import pickle
from dataclasses import dataclass

import pytest

from citry import Citry, Component, Const, Secret
from citry._app_selection import CheckAppSelection
from citry._checker import check_project
from citry._json_wire import json_wire_type_from_annotation

try:
    import pydantic
except ImportError:
    pydantic = None  # type: ignore[assignment]

# The m42 benchmark app's constants, with the token wrapped.
API_BASE = "/api"
SECRET_TOKEN = Secret("s3cr3t")
# A Secret nested inside a plain constant, sent by name.
API_CONFIG = {"base": "/api", "keys": ["public", Secret("s3cr3t")]}

_JS_DATA = "citry.js-data.unsupported-type"
_SECRET_DETAIL = "Secret values are never sent to the browser; read the value on the server instead"  # noqa: S105
_COMPONENT_JS = """
    $component({});
"""


################################################
# THE SECRET CLASS
################################################


def test_every_text_form_of_a_secret_is_masked():
    token = Secret("s3cr3t")

    assert str(token) == "***"
    assert repr(token) == "Secret('***')"
    assert f"{token}" == "***"
    assert f"{token:>5}" == "  ***"
    assert "s3cr3t" not in str([token, {"token": token}])


def test_the_value_is_read_with_get_secret_value():
    assert Secret("s3cr3t").get_secret_value() == "s3cr3t"
    assert Secret(b"raw").get_secret_value() == b"raw"
    # The subscripted form used in annotations also constructs one.
    assert Secret[str]("s3cr3t").get_secret_value() == "s3cr3t"


def test_a_secret_cannot_be_changed():
    token = Secret("s3cr3t")

    with pytest.raises(AttributeError, match="Secret is immutable"):
        token._secret_value = "other"  # type: ignore[misc]  # noqa: S105
    with pytest.raises(AttributeError, match="Secret is immutable"):
        del token._secret_value
    assert token.get_secret_value() == "s3cr3t"


def test_wrapping_a_secret_again_is_refused():
    with pytest.raises(TypeError, match="already a Secret"):
        Secret(Secret("s3cr3t"))


def test_equality_and_hashing_follow_the_value():
    assert Secret("a") == Secret("a")
    assert Secret("a") != Secret("b")
    # A plain value never equals a Secret, so a guessed string cannot match.
    assert Secret("a") != "a"
    assert hash(Secret("a")) == hash(Secret("a"))
    assert {Secret("a"): 1}[Secret("a")] == 1
    with pytest.raises(TypeError, match="unhashable"):
        hash(Secret(["a"]))


def test_truth_follows_the_value():
    assert Secret("s3cr3t")
    assert not Secret("")


@pytest.mark.parametrize("clone", [copy.copy, copy.deepcopy, lambda value: pickle.loads(pickle.dumps(value))])  # noqa: S301
def test_copies_and_pickles_keep_the_value(clone):
    copied = clone(Secret("s3cr3t"))

    assert type(copied) is Secret
    assert copied.get_secret_value() == "s3cr3t"


################################################
# RUNTIME: js_data() REFUSES A SECRET
################################################


def _board_page(engine: Citry, js_data):
    """Build the m42 board page, with a js_data() that returns `js_data`."""

    def js_data_method(self, kwargs, slots):
        return js_data

    return type(
        "BoardPage",
        (Component,),
        {
            "citry": engine,
            "template": "<p>Board</p>",
            "js": _COMPONENT_JS,
            "js_data": js_data_method,
        },
    )


def test_m42_a_secret_returned_from_js_data_fails_the_render():
    board = _board_page(
        Citry(autodiscover=False),
        {"apiBase": API_BASE, "hiddenTitles": [], "secretToken": SECRET_TOKEN},
    )

    with pytest.raises(TypeError) as error:
        str(board())

    message = str(error.value)
    assert message.startswith(
        'BoardPage.js_data()["secretToken"] holds a citry.Secret, and Citry never sends a Secret to the browser'
    )
    assert "leave it out of js_data()" in message
    assert "s3cr3t" not in message


@pytest.mark.parametrize(
    ("js_data", "path"),
    [
        ({"config": {"token": SECRET_TOKEN}}, '["config"]["token"]'),
        ({"rows": [1, {"token": SECRET_TOKEN}]}, '["rows"][1]["token"]'),
        ({"pair": ("public", SECRET_TOKEN)}, '["pair"][1]'),
        # A Const marker is looked through, as the JSON conversion does.
        ({"token": Const(SECRET_TOKEN)}, '["token"]'),
        ({"config": Const({"token": SECRET_TOKEN})}, '["config"]["token"]'),
    ],
)
def test_a_nested_secret_is_named_by_its_key_path(js_data, path):
    board = _board_page(Citry(autodiscover=False), js_data)

    with pytest.raises(TypeError, match=r"^BoardPage\.js_data\(\)" + path.replace("[", r"\[").replace("]", r"\]")):
        str(board())


def test_a_secret_jsdata_field_fails_the_render():
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine
        template = "<p></p>"
        js = _COMPONENT_JS

        class JsData:
            token: Secret[str]

        def js_data(self, kwargs, slots):
            return self.JsData(token=SECRET_TOKEN)

    with pytest.raises(TypeError, match=r'^Page\.js_data\(\)\["token"\] holds a citry\.Secret'):
        str(Page())


def test_a_secret_inside_a_dataclass_is_refused_with_the_dataclass():
    # JSON cannot carry the dataclass itself, so the render fails on it
    # before it looks inside; the secret is not sent either way.
    @dataclass
    class Settings:
        token: Secret[str]

    board = _board_page(Citry(autodiscover=False), {"settings": Settings(token=SECRET_TOKEN)})

    with pytest.raises(TypeError, match="got Settings") as error:
        str(board())
    assert "s3cr3t" not in str(error.value)


################################################
# RUNTIME: css_data() AND STATE REFUSE A SECRET
################################################


def test_a_secret_in_css_data_fails_the_render():
    engine = Citry(autodiscover=False)

    class Banner(Component):
        citry = engine
        template = "<p>Banner</p>"
        css = """
            p { color: var(--token); }
        """

        def css_data(self, kwargs, slots):
            return {"token": SECRET_TOKEN}

    with pytest.raises(ValueError, match=r"css_data\(\) entry 'token' cannot be emitted: it holds a citry\.Secret"):
        str(Banner())


def test_a_secret_in_state_fails_the_render():
    engine = Citry(autodiscover=False)

    class Panel(Component):
        citry = engine
        template = """
            <button @click="$sendEvent('refresh')">Refresh</button>
        """

        class Kwargs:
            token: Secret[str]

        class State:
            token: Secret[str]

        class Events:
            def refresh(self, state, request):
                return None

    with pytest.raises(ValueError, match=r"State field 'token' holds a citry\.Secret") as error:
        str(Panel(token=SECRET_TOKEN))
    assert "s3cr3t" not in str(error.value)


################################################
# RUNTIME: A SECRET STAYS USABLE ON THE SERVER
################################################


def test_a_secret_renders_as_masked_text_in_a_template():
    engine = Citry(autodiscover=False)

    class Header(Component):
        citry = engine
        template = """
            <p c-title="token">{{ token }}</p>
        """

        def template_data(self, kwargs, slots):
            return {"token": SECRET_TOKEN}

    html = str(Header())

    assert ">***</p>" in html
    assert 'title="***"' in html
    assert "s3cr3t" not in html


def test_a_vue_component_may_use_a_secret_in_template_data():
    # The secret is read on the server; only the derived value is sent.
    engine = Citry(autodiscover=False)

    class Board(Component):
        citry = engine
        template = """
            <p>{{ token }} {{ count }}</p>
        """
        js = _COMPONENT_JS

        def template_data(self, kwargs, slots):
            return {"token": SECRET_TOKEN, "count": len(SECRET_TOKEN.get_secret_value())}

        def js_data(self, kwargs, slots):
            return {"apiBase": API_BASE, "hiddenTitles": []}

    html = str(Board())

    assert "*** 6" in html
    assert "s3cr3t" not in html


def test_a_secret_passed_to_a_child_component_stays_on_the_server():
    engine = Citry(autodiscover=False)

    class TokenBadge(Component):
        citry = engine
        template = """
            <span>{{ token }} ({{ size }})</span>
        """

        class Kwargs:
            token: Secret[str]

        def template_data(self, kwargs, slots):
            return {"token": kwargs.token, "size": len(kwargs.token.get_secret_value())}

    class VueBadge(Component):
        # A child with browser code: its kwargs are not sent, only js_data().
        citry = engine
        template = """
            <span>{{ token }}</span>
        """
        js = _COMPONENT_JS

        class Kwargs:
            token: Secret[str]

        def js_data(self, kwargs, slots):
            return {"ready": True}

    class Page(Component):
        citry = engine
        template = """
            <c-TokenBadge c-token="token" />
            <c-VueBadge c-token="token" />
        """

        def template_data(self, kwargs, slots):
            return {"token": SECRET_TOKEN}

    html = str(Page())

    assert "*** (6)" in html
    assert "s3cr3t" not in html


def test_a_secret_annotation_accepts_a_secret_and_hides_a_bare_value():
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
            <p>{{ token }}</p>
        """

        class Kwargs:
            token: Secret[str] | None = None

    assert "***" in str(Card(token=SECRET_TOKEN))
    # The bare value is most likely the secret, so the error does not print it.
    with pytest.raises(TypeError, match=r"Card\.Kwargs\.token expects .*Secret\[str\] \| None, got .*str") as error:
        str(Card(token="s3cr3t"))  # noqa: S106
    assert "s3cr3t" not in str(error.value)
    assert "as Secret(value)" in str(error.value)


def test_a_plain_value_for_a_list_of_secrets_is_hidden_too():
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
            <p>{{ tokens }}</p>
        """

        class Kwargs:
            tokens: list[Secret[str]]

    with pytest.raises(TypeError, match=r"value hidden") as error:
        str(Card(tokens="s3cr3t"))
    assert "s3cr3t" not in str(error.value)


def test_a_plain_value_in_a_secret_jsdata_field_says_to_remove_the_field():
    # Wrapping the value would only fail the render later, so the advice
    # for a field that goes to the browser is to drop it.
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine
        template = "<p></p>"
        js = _COMPONENT_JS

        class JsData:
            token: Secret[str]

        def js_data(self, kwargs, slots):
            return {"token": "s3cr3t"}

    with pytest.raises(TypeError, match=r"got str \(value hidden\)\. .*a JsData field cannot hold one") as error:
        str(Page())
    assert "s3cr3t" not in str(error.value)


@pytest.mark.skipif(pydantic is None, reason="needs pydantic")
def test_a_pydantic_kwargs_field_accepts_a_secret():
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = """
            <p>{{ token }}</p>
        """

        class Kwargs(pydantic.BaseModel):
            token: Secret[str]

    assert "<p" in str(Card(token=SECRET_TOKEN))
    with pytest.raises(pydantic.ValidationError):
        str(Card(token="s3cr3t"))  # noqa: S106


def test_a_plain_string_secret_is_still_sent():
    # Citry detects only wrapped values; a bare string is ordinary data.
    board = _board_page(Citry(autodiscover=False), {"secretToken": "s3cr3t"})

    assert "s3cr3t" in str(board())


################################################
# STATIC: citry check WARNS BEFORE THE PAGE RUNS
################################################


def _findings(engine: Citry, tmp_path) -> list[tuple[str, str]]:
    report = check_project(CheckAppSelection(spec="app:engine", engine=engine), tmp_path)
    return [(item.severity, item.message) for item in report.findings if item.code == _JS_DATA]


_M42_ENGINE = Citry(autodiscover=False)


class M42BoardPage(Component):
    citry = _M42_ENGINE
    template = "<p>Board</p>"

    def js_data(self, kwargs, slots):
        return {"apiBase": API_BASE, "hiddenTitles": [], "secretToken": SECRET_TOKEN}


class M42ConfigPage(Component):
    citry = _M42_ENGINE
    template = "<p>Config</p>"

    def js_data(self, kwargs, slots):
        return {"config": API_CONFIG}


class M42NestedPage(Component):
    citry = _M42_ENGINE
    template = "<p>Nested</p>"

    def js_data(self, kwargs, slots):
        return {"auth": {"token": SECRET_TOKEN}, "keys": [API_BASE, SECRET_TOKEN]}


_NEVER_SENT_ADVICE = (
    "holds a citry.Secret, which Citry never sends to the browser; read the value on the server instead."
    " Browser tooling will treat its type as unknown"
)


def test_m42_check_reports_a_secret_module_constant(tmp_path):
    assert _findings(_M42_ENGINE, tmp_path) == [
        (
            "warning",
            f"JsData field 'secretToken' is not a clean JSON value: SECRET_TOKEN {_NEVER_SENT_ADVICE}.",
        ),
        (
            "warning",
            f"JsData field 'config' is not a clean JSON value: API_CONFIG[\"keys\"][1] {_NEVER_SENT_ADVICE}.",
        ),
        # A name written inside a dict or list literal is read too.
        ("warning", f"JsData field 'auth' is not a clean JSON value: SECRET_TOKEN {_NEVER_SENT_ADVICE}."),
        ("warning", f"JsData field 'keys' is not a clean JSON value: SECRET_TOKEN {_NEVER_SENT_ADVICE}."),
    ]


_ANNOTATION_ENGINE = Citry(autodiscover=False)


class SecretFieldPage(Component):
    citry = _ANNOTATION_ENGINE
    template = "<p></p>"

    class JsData:
        token: Secret[str]
        label: str


class SecretKwargsPage(Component):
    citry = _ANNOTATION_ENGINE
    template = "<p></p>"

    class Kwargs:
        token: Secret[str]

    def js_data(self, kwargs: Kwargs, slots):
        return {"token": kwargs.token}


def test_check_reports_a_secret_jsdata_field_and_kwargs_value(tmp_path):
    message = (
        f"JsData field 'token' is not a clean JSON value: {_SECRET_DETAIL}."
        " Browser tooling will treat its type as unknown."
    )

    assert _findings(_ANNOTATION_ENGINE, tmp_path) == [("warning", message), ("warning", message)]


_SILENT_ENGINE = Citry(autodiscover=False)


class SecretBadge(Component):
    citry = _SILENT_ENGINE
    template = """
        <span>{{ token }}</span>
    """

    class Kwargs:
        token: Secret[str]


class ServerOnlyBoard(Component):
    citry = _SILENT_ENGINE
    template = """
        <c-SecretBadge c-token="token" />
    """
    js = _COMPONENT_JS

    class JsData:
        title: str

    def template_data(self, kwargs, slots):
        return {"token": SECRET_TOKEN}

    def js_data(self, kwargs, slots):
        return self.JsData(title="Board")


class PlainDataBoard(Component):
    citry = _SILENT_ENGINE
    template = "<p></p>"

    def js_data(self, kwargs, slots):
        size = len(SECRET_TOKEN.get_secret_value())
        # A name used inside a call sends what the call returns.
        return {"apiBase": API_BASE, "tokenLength": size, "tokenSet": bool(SECRET_TOKEN)}


def test_check_is_silent_when_a_secret_stays_on_the_server(tmp_path):
    assert _findings(_SILENT_ENGINE, tmp_path) == []


def test_a_secret_annotation_object_is_described_by_its_import_path():
    # This module's annotations are strings; a class built at runtime holds
    # the real `Secret[str]` objects, which introspection must still name.
    engine = Citry(autodiscover=False)
    schema = type("JsData", (), {"__annotations__": {"token": Secret[str], "maybe": Secret[bytes] | None}})
    page = type("Page", (Component,), {"citry": engine, "template": "<p></p>", "JsData": schema})

    fields = engine.inspect_component(page).schemas.js_data.fields

    assert [(item.name, item.type_display) for item in fields] == [
        ("token", "citry.secret.Secret[str]"),
        ("maybe", "citry.secret.Secret[bytes] | None"),
    ]


@pytest.mark.parametrize(
    "annotation",
    [
        "Secret[str]",
        "Secret",
        "citry.Secret[bytes]",
        "citry.secret.Secret[str] | None",
        "list[Secret[str]]",
        "dict[str, Secret[str]]",
    ],
)
def test_every_spelling_of_a_secret_annotation_is_not_json(annotation):
    assert json_wire_type_from_annotation(annotation).unsupported == (_SECRET_DETAIL,)
