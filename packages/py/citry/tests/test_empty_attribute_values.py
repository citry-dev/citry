"""
A written empty value (``alt=""``) on a component tag passes ``""``, while a
bare attribute (``alt``) passes ``True``. HTML elements, a dynamic
``<c-element>``, ``<c-if cond="">``, and the attributes that configure
``<c-slot>`` and ``<c-fill>`` treat an empty value as the bare form.
"""

import re

import pytest

from citry import Citry, Component


def _recorder(c, annotation):
    """Register an ``Avatar`` component that stores the ``alt`` it receives."""
    seen = []

    class Kwargs:
        __annotations__ = {"alt": annotation}

    def template_data(self, kwargs, slots):
        seen.append(kwargs.alt)
        return {"alt": repr(kwargs.alt)}

    # The annotation differs per test, so the Kwargs class is built at run time.
    type(
        "Avatar",
        (Component,),
        {"citry": c, "Kwargs": Kwargs, "template": "<p>{{ alt }}</p>", "template_data": template_data},
    )
    return seen


_page_count = 0


def _render(c, template):
    global _page_count  # noqa: PLW0603
    _page_count += 1
    page = type(f"Page{_page_count}", (Component,), {"citry": c, "template": template})
    return page().render().serialize()


class TestComponentInputs:
    def test_written_empty_value_passes_empty_string(self):
        c = Citry()
        seen = _recorder(c, str)

        _render(c, '<c-Avatar alt="" />')
        _render(c, "<c-Avatar alt='' />")

        assert seen == ["", ""]

    def test_bare_attribute_passes_true(self):
        c = Citry()
        seen = _recorder(c, bool | str)

        _render(c, "<c-Avatar alt />")
        _render(c, '<c-Avatar alt="" />')

        assert seen == [True, ""]

    def test_empty_value_on_bool_input_explains_the_bare_form(self):
        c = Citry()

        class Grid(Component):
            citry = c

            class Kwargs:
                compact: bool

            template = "<p>{{ compact }}</p>"

        with pytest.raises(TypeError, match=r"write compact without a value, as in <c-Grid compact />, to pass True"):
            _render(c, '<c-Grid compact="" />')
        assert "True" in _render(c, "<c-Grid compact />")

    def test_c_component_forwards_empty_string(self):
        c = Citry()
        seen = _recorder(c, str)

        _render(c, '<c-component is="avatar" alt="" />')

        assert seen == [""]


class TestSlotData:
    def test_slot_data_empty_value_reaches_fill_as_empty_string(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="item" x="" y /></div>'

        html = _render(c, '<c-card><c-fill name="item" data="d">[{{ d.x }}]|{{ d.y }}</c-fill></c-card>')

        assert "[]|True</div>" in html


class TestUnchangedBareForm:
    def test_dynamic_element_renders_empty_class_bare(self):
        c = Citry()

        html = _render(c, '<c-element c-is="\'p\'" class="">x</c-element>')

        assert "class " in html
        assert 'class=""' not in html

    def test_dynamic_element_renders_empty_attribute_bare(self):
        c = Citry()

        html = _render(c, '<c-element c-is="\'img\'" alt="" />')

        assert " alt " in html
        assert 'alt=""' not in html

    def test_html_element_empty_value_renders_bare(self):
        c = Citry()

        # An HTML element writes an empty value as a bare attribute.
        assert re.sub(r' data-cid-\w+=""', "", _render(c, '<img alt="">')) == '<img alt="">'

    def test_if_with_empty_cond_renders_body(self):
        c = Citry()

        assert _render(c, '<c-if cond="">body</c-if>') == "body"


class TestBuiltInTags:
    def test_required_written_empty_still_makes_a_slot_required(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = """
<div><c-slot name="item" required="" /></div>
"""

        # `required` configures the slot, so `required=""` means required,
        # as a bare `required` does.
        with pytest.raises(RuntimeError, match="is marked as required"):
            _render(c, "<c-Card></c-Card>")

    def test_provide_receives_an_empty_value_as_text(self):
        c = Citry()

        class Reader(Component):
            citry = c
            template = """
<p>{{ value }}</p>
"""

            def template_data(self, kwargs, slots):
                return {"value": repr(self.inject("box").label)}

        html = _render(c, '<c-provide key="box" label=""><c-Reader /></c-provide>')
        # repr("") is '', escaped in the page.
        assert ">&#39;&#39;</p>" in html

    def test_cache_enabled_written_empty_explains_the_bare_form(self):
        c = Citry()
        with pytest.raises(ValueError, match="Write enabled without a value"):
            _render(c, '<c-cache key="k" enabled="">x</c-cache>')

    def test_i18n_client_written_empty_explains_the_bare_form(self):
        c = Citry()
        with pytest.raises(TypeError, match="Write client without a value"):
            _render(c, '<c-i18n client="">x</c-i18n>')


class TestHint:
    def test_an_int_input_gets_no_bool_hint(self):
        c = Citry()

        class Counter(Component):
            citry = c
            template = """
<p>{{ v }}</p>
"""

            class Kwargs:
                v: int = 0

        # A bare attribute passes True, which an int input accepts; the hint
        # must not read that as the input wanting a bool.
        _render(c, "<c-Counter v />")
        with pytest.raises(TypeError) as error:
            _render(c, '<c-Counter v="" />')
        assert "without a value" not in str(error.value)

    def test_the_hint_names_a_registered_component_name(self):
        c = Citry()

        class Grid(Component):
            citry = c
            name = "layout-grid"
            template = """
<p>{{ compact }}</p>
"""

            class Kwargs:
                compact: bool = False

        with pytest.raises(TypeError, match=re.escape("as in <c-layout-grid compact />")):
            _render(c, '<c-layout-grid compact="" />')
