"""Guarded result conversion preserves live component protocols and escaping."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import citry.citry_render as renders
from citry import Citry, Component, Const, Markup, Slot
from citry.citry_context import CitryContext


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ""),
        ("<&", Markup("&lt;&amp;")),
        ("", Markup("")),
        (1, Markup("1")),
        (False, Markup("False")),
        (Markup("<b>"), Markup("<b>")),
        (Const("<&"), Markup("&lt;&amp;")),
    ],
)
def test_scalar_type_text_and_escaping(value, expected):
    actual = renders._render_value(value)
    assert type(actual) is type(expected)
    assert actual == expected


def test_render_identity_and_slot_callback_stay_live():
    value = renders.CitryRender([], CitryContext())
    assert renders._render_value(value) is value
    assert renders._render_value(Const(value)) is value
    calls = []

    def content(ctx):
        calls.append(ctx)
        return value

    slot = Slot(content)
    assert renders._render_value(slot) is value
    assert renders._render_value(slot) is value
    assert len(calls) == 2


@pytest.mark.parametrize("placement", ["subclass", "instance", "render_class"])
def test_protocol_members_resolve_once_per_call(monkeypatch, placement):
    app = Citry(autodiscover=False)
    calls = []

    class Text(Component):
        citry = app
        template = """
            <span>resolved</span>
        """

    def resolve(_self, engine):
        calls.append(engine)
        return Text()

    class CustomRender(renders.CitryRender):
        pass

    if placement == "subclass":
        CustomRender.__citry_element__ = resolve
        value = CustomRender([], CitryContext())
    elif placement == "instance":
        value = CustomRender([], CitryContext())
        value.__citry_element__ = lambda engine: resolve(value, engine)
    else:
        value = renders.CitryRender([], CitryContext())
        assert renders._render_value(value) is value
        monkeypatch.setattr(renders.CitryRender, "__citry_element__", resolve, raising=False)
    for _ in range(2):
        result = renders._render_value(value, citry=app)
        assert isinstance(result.context.component, Text)
    assert calls == [app, app]


@pytest.mark.parametrize("name", ["CitryRender", "PhysicalRegionPart"])
@pytest.mark.parametrize("warm", [False, True])
def test_structural_type_alias_replacements_preserve_unescaped_text(monkeypatch, name, warm):
    if warm:
        assert renders._render_value("<") == "&lt;"
    monkeypatch.setattr(renders, name, str)
    result = renders._render_value("<")
    assert type(result) is str
    assert result == "<"


def test_replacement_render_class_keeps_instance_protocol(monkeypatch):
    class Replacement:
        pass

    value = Replacement()

    def fail(_engine):
        raise LookupError("live resolver")

    value.__citry_element__ = fail
    monkeypatch.setattr(renders, "CitryRender", Replacement)
    with pytest.raises(LookupError, match="live resolver"):
        renders._render_value(value, citry=Citry(autodiscover=False))


@pytest.mark.parametrize(("name", "missing"), [("ComponentLike", "__citry_element__"), ("CitryElement", "comp_cls")])
@pytest.mark.parametrize("warm", [False, True])
def test_other_dispatch_alias_replacements_preserve_errors(monkeypatch, name, missing, warm):
    if warm:
        assert renders._render_value("<") == "&lt;"
    monkeypatch.setattr(renders, name, str)
    with pytest.raises(AttributeError) as caught:
        renders._render_value("<", citry=Citry(autodiscover=False))
    assert str(caught.value) == f"'str' object has no attribute '{missing}'"


def test_const_unwrapper_and_escaper_overrides_stay_live(monkeypatch):
    calls = []

    def unwrap(value):
        calls.append(("unwrap", value))
        return "replacement"

    def escape(value):
        calls.append(("escape", value))
        return Markup("escaped")

    monkeypatch.setattr(renders, "const_value", unwrap)
    monkeypatch.setattr(renders, "escape", escape)
    value = renders.CitryRender([], CitryContext())
    for _ in range(2):
        assert renders._render_value(value) == "escaped"
    assert calls == [("unwrap", value), ("escape", "replacement")] * 2


@pytest.mark.parametrize("type_name", ["str", "renders.CitryRender"])
def test_explicit_protocol_registration_preserves_missing_method_error(type_name):
    # Registration survives individual renders, so keep it out of other tests.
    source = f"""
import citry.citry_render as renders
from citry import Citry
from citry.citry_context import CitryContext
value = '<' if {type_name} is str else renders.CitryRender([], CitryContext())
first = renders._render_value(value)
assert first == '&lt;' if type(value) is str else first is value
renders.ComponentLike.register({type_name})
for _ in range(2):
    try:
        renders._render_value(value, citry=Citry(autodiscover=False))
    except AttributeError as error:
        assert str(error) == f"'{{type(value).__name__}}' object has no attribute '__citry_element__'"
    else:
        raise AssertionError('Registered protocol type skipped resolution')
"""
    package_root = str(Path(renders.__file__).resolve().parent.parent)
    result = subprocess.run(
        [sys.executable, "-c", source],
        env={**os.environ, "PYTHONPATH": os.pathsep.join((package_root, os.environ.get("PYTHONPATH", "")))},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("owner", "name", "missing"),
    [
        ("citry.citry_element", "CitryElement", "comp_cls"),
        ("citry.component_like", "ComponentLike", "__citry_element__"),
    ],
)
def test_alias_replaced_before_render_module_reload_is_not_trusted(owner, name, missing):
    # Reloading creates new local render classes. Imported replacement aliases
    # must still differ from the identities saved where those types were defined.
    source = f"""
import importlib
import citry.citry_render as renders
from citry import Citry
owner = importlib.import_module({owner!r})
class Meta(type):
    def __instancecheck__(cls, value):
        return True
    def __subclasscheck__(cls, value):
        return False
class Replacement(metaclass=Meta):
    pass
setattr(owner, {name!r}, str if {name!r} == 'CitryElement' else Replacement)
renders = importlib.reload(renders)
try:
    renders._render_value('<', citry=Citry(autodiscover=False))
except AttributeError as error:
    assert str(error) == {f"'str' object has no attribute '{missing}'"!r}
else:
    raise AssertionError('Preinstalled alias became trusted')
"""
    package_root = str(Path(renders.__file__).resolve().parent.parent)
    result = subprocess.run(
        [sys.executable, "-c", source],
        env={**os.environ, "PYTHONPATH": os.pathsep.join((package_root, os.environ.get("PYTHONPATH", "")))},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
