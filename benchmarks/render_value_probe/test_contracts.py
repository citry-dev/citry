"""Dynamic dispatch cases that would invalidate the result-conversion shortcut."""

# ruff: noqa: ANN001, ANN201, ANN202, S101

import inspect
import subprocess
import sys

import pytest
from probe import ORIGINAL, TRUSTED_RENDER, candidate, renders

from citry import Citry, Component, Const, Markup, Slot
from citry.citry_context import CitryContext

pytestmark = pytest.mark.skipif(
    "_DEFAULT_VALUE_TYPES" in inspect.getsource(ORIGINAL),
    reason="These prototype comparisons require the pre-production checkout; production has package regressions",
)


@pytest.mark.parametrize("value", [None, "<&", "", 1, False, Markup("<b>"), Const("<&")])
def test_scalar_type_text_and_escaping(value):
    expected = ORIGINAL(value)
    actual = candidate()(value)
    assert type(actual) is type(expected)
    assert actual == expected


def test_render_identity_and_slot_callback_stay_live():
    changed = candidate()
    value = TRUSTED_RENDER([], CitryContext())
    assert changed(value) is value
    assert changed(Const(value)) is value
    calls = []

    def content(ctx):
        calls.append(ctx)
        return value

    slot = Slot(content)
    assert changed(slot) is value
    assert changed(slot) is value
    assert len(calls) == 2


@pytest.mark.parametrize("placement", ["subclass", "instance", "render_class"])
def test_protocol_members_resolve_once_per_call(monkeypatch, placement):
    changed = candidate()
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

    class CustomRender(TRUSTED_RENDER):
        pass

    if placement == "subclass":
        CustomRender.__citry_element__ = resolve
        value = CustomRender([], CitryContext())
    elif placement == "instance":
        value = CustomRender([], CitryContext())
        value.__citry_element__ = lambda engine: resolve(value, engine)
    else:
        value = TRUSTED_RENDER([], CitryContext())
        # The class acquires behavior after the shortcut has already been used.
        assert changed(value) is value
        monkeypatch.setattr(TRUSTED_RENDER, "__citry_element__", resolve, raising=False)
    for function in (ORIGINAL, changed):
        result = function(value, citry=app)
        assert isinstance(result.context.component, Text)
    assert calls == [app, app]


@pytest.mark.parametrize("name", ["CitryRender", "PhysicalRegionPart"])
@pytest.mark.parametrize("before", [False, True])
def test_structural_type_alias_replacements_preserve_unescaped_text(monkeypatch, name, before):
    changed = None if before else candidate()
    monkeypatch.setattr(renders, name, str)
    changed = candidate() if before else changed
    assert ORIGINAL("<") == "<"
    result = changed("<")
    assert type(result) is str
    assert result == "<"


def test_preinstalled_replacement_render_class_keeps_instance_protocol(monkeypatch):
    class Replacement:
        pass

    value = Replacement()

    def fail(_engine):
        raise LookupError("live resolver")

    value.__citry_element__ = fail
    monkeypatch.setattr(renders, "CitryRender", Replacement)
    changed = candidate()
    for function in (ORIGINAL, changed):
        with pytest.raises(LookupError, match="live resolver"):
            function(value, citry=Citry(autodiscover=False))


@pytest.mark.parametrize("name", ["ComponentLike", "CitryElement"])
@pytest.mark.parametrize("before", [False, True])
def test_other_dispatch_alias_replacements_preserve_errors(monkeypatch, name, before):
    changed = None if before else candidate()
    monkeypatch.setattr(renders, name, str)
    changed = candidate() if before else changed
    errors = []
    for function in (ORIGINAL, changed):
        with pytest.raises(AttributeError) as caught:
            function("<", citry=Citry(autodiscover=False))
        errors.append((type(caught.value), str(caught.value)))
    assert errors[0] == errors[1]


def test_const_unwrapper_and_escaper_overrides_stay_live(monkeypatch):
    changed = candidate()
    calls = []

    def unwrap(value):
        calls.append(("unwrap", value))
        return "replacement"

    def escape(value):
        calls.append(("escape", value))
        return Markup("escaped")

    monkeypatch.setattr(renders, "const_value", unwrap)
    monkeypatch.setattr(renders, "escape", escape)
    value = TRUSTED_RENDER([], CitryContext())
    for function in (ORIGINAL, changed):
        assert function(value) == "escaped"
    assert calls == [("unwrap", value), ("escape", "replacement")] * 2


@pytest.mark.parametrize("type_name", ["str", "TRUSTED_RENDER"])
def test_explicit_protocol_registration_preserves_missing_method_error(type_name):
    # ABC registration is permanent, so isolate it from later scenario renders.
    source = f"""
from probe import ORIGINAL, TRUSTED_RENDER, candidate, renders
from citry import Citry
from citry.citry_context import CitryContext
changed = candidate()
renders.ComponentLike.register({type_name})
value = '<' if {type_name} is str else TRUSTED_RENDER([], CitryContext())
errors = []
for function in (ORIGINAL, changed):
    try:
        function(value, citry=Citry(autodiscover=False))
    except Exception as error:
        errors.append((type(error).__name__, str(error)))
assert len(errors) == 2 and errors[0] == errors[1], errors
assert errors[0][0] == 'AttributeError', errors
"""
    result = subprocess.run(
        [sys.executable, "-c", source], cwd=__file__.rsplit("/", 1)[0], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
