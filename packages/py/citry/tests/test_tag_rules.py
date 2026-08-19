"""
Tests for parse-time validation of component usage (citry/tag_rules.py).

A component's ``Kwargs``/``Slots`` declarations become parser ``user_rules``,
so a template that uses the component with unknown or missing kwargs/fills
fails when the template is parsed (at the parent's first render), not at
render time and not silently.
"""

import importlib
import threading
from typing import ClassVar, NamedTuple, TypedDict

import pytest

from citry import Citry, CitryLifecycleInProgress, Component, SlotInput
from citry.tag_rules import build_tag_rules
from citry_core.template_parser import TagRules, parse_template


class _BaseRowSlotData:
    item: str
    ignored: ClassVar[str]


class _RowSlotData(_BaseRowSlotData):
    index: int


class _EmptySlotData:
    pass


def _declared_card(c):
    class Card(Component):
        citry = c
        template = '<div>{{ title }}<c-slot name="header" /></div>'

        class Kwargs:
            title: str
            size: int = 10

        class Slots:
            header: SlotInput
            footer: "SlotInput | None" = None

        def template_data(self, kwargs, slots):
            return {"title": kwargs.title}

    return Card


class TestBuildTagRules:
    def test_rules_derived_from_declarations(self):
        c = Citry()
        _declared_card(c)
        rules = build_tag_rules(c)

        card_rules = rules["c-card"]
        assert card_rules.allowed_attrs == [
            ["title", "c-title"],
            ["size", "c-size"],
            ["c-if"],
            ["c-elif"],
            ["c-else"],
            ["c-for"],
            ["c-empty"],
        ]
        assert card_rules.required_attrs == [["title", "c-title"]]
        assert card_rules.allowed_slots == ["header", "footer"]
        assert card_rules.required_slots == ["header"]
        assert card_rules.slot_data_fields == {}

    def test_slot_data_fields_derived_from_parameterized_slot_inputs(self):
        c = Citry()

        class Grid(Component):
            citry = c
            template = '<c-slot name="row" />'

            class Slots:
                row: "SlotInput[_RowSlotData] | None" = None
                empty: SlotInput[_EmptySlotData] | None = None
                opaque: SlotInput | None = None
                unresolved: "SlotInput[MissingSlotData] | None" = None  # noqa: F821 - intentionally unresolved

        rules = build_tag_rules(c)["c-grid"]
        assert rules.slot_data_fields == {
            "empty": [],
            "row": ["item", "index"],
        }

    def test_component_nested_slot_data_shape_resolves(self):
        c = Citry()

        class Grid(Component):
            citry = c
            template = '<c-slot name="default" />'

            class ItemSlotData:
                item: str

            class Slots:
                default: "SlotInput[ItemSlotData]"  # noqa: F821 - resolved from the component namespace

        assert build_tag_rules(c)["c-grid"].slot_data_fields == {"default": ["item"]}

    def test_parameterized_builtin_slot_data_shape_stays_open(self):
        c = Citry()

        class Layout(Component):
            citry = c
            template = '<c-slot name="body" />'

            class Slots:
                body: SlotInput[dict[str, object]]

        assert build_tag_rules(c)["c-layout"].slot_data_fields == {}

    def test_slot_data_fields_support_schema_adapters(self):
        c = Citry()

        class NamedData(NamedTuple):
            item: str
            index: int

        class DictData(TypedDict):
            item: str
            selected: bool

        class ModelData(_FakeModelBase):
            model_fields = {
                "item": _FakeFieldInfo(required=True),
                "disabled": _FakeFieldInfo(required=False),
            }

        class Grid(Component):
            citry = c
            template = "<div></div>"

            class Slots:
                named: SlotInput[NamedData]
                mapping: SlotInput[DictData]
                model: SlotInput[ModelData]

        assert build_tag_rules(c)["c-grid"].slot_data_fields == {
            "mapping": ["item", "selected"],
            "model": ["item", "disabled"],
            "named": ["item", "index"],
        }

    def test_undeclared_component_gets_no_rules(self):
        c = Citry()

        class Plain(Component):
            citry = c
            template = "<p>x</p>"

        assert "c-plain" not in build_tag_rules(c)

    def test_kwargs_only_leaves_slots_unrestricted(self):
        c = Citry()

        class KwOnly(Component):
            citry = c
            template = "<p>x</p>"

            class Kwargs:
                title: str

        rules = build_tag_rules(c)["c-kw-only"]
        assert rules.allowed_slots is None
        assert rules.required_slots == []
        assert rules.allowed_attrs is not None

    def test_rules_for_both_registered_name_forms(self):
        c = Citry()

        class MyCard(Component):
            citry = c
            template = "<p>x</p>"

            class Kwargs:
                title: str

        rules = build_tag_rules(c)
        assert "c-mycard" in rules
        assert "c-my-card" in rules

    def test_cache_invalidated_on_register(self):
        c = Citry()
        # A fresh instance carries only the built-ins' rules (the
        # <c-cache>, <c-error-fallback>, and <c-i18n> declare typed inputs).
        assert set(c._tag_rules()) == {"c-cache", "c-error-fallback", "c-i18n"}

        _declared_card(c)
        assert "c-card" in c._tag_rules()

    def test_template_parsing_populates_separate_instance_caches(self):
        c1 = Citry()
        c2 = Citry()
        _declared_card(c1)

        class PageOne(Component):
            citry = c1
            template = '<c-card title="T"><c-fill name="header">H</c-fill></c-card>'

        class PageTwo(Component):
            citry = c2
            template = "<p>x</p>"

        assert c1._tag_rules_cache is None
        assert c2._tag_rules_cache is None

        str(PageOne())
        str(PageTwo())

        assert c1._tag_rules_cache is not None
        assert c2._tag_rules_cache is not None
        assert c1._tag_rules_cache is not c2._tag_rules_cache
        assert "c-card" in c1._tag_rules_cache
        assert "c-card" not in c2._tag_rules_cache

    def test_concurrent_registration_cannot_publish_stale_rules(self, monkeypatch):
        app = Citry(autodiscover=False)

        class TypedCard(Component):
            citry = app
            template = """
            <p>{{ title }}</p>
            """

            class Kwargs:
                title: str

        app.unregister(TypedCard)
        app.initialize()
        app._tag_rules_cache = None
        started = threading.Event()
        release = threading.Event()
        owner_errors: list[BaseException] = []
        rules_module = importlib.import_module("citry.citry")
        original_build_tag_rules = rules_module.build_tag_rules
        first_build = True

        def paused_build_tag_rules(citry_instance):
            nonlocal first_build
            rules = original_build_tag_rules(citry_instance)
            if first_build:
                first_build = False
                started.set()
                assert release.wait(5)
            return rules

        def build_rules():
            try:
                app._tag_rules()
            except BaseException as err:  # noqa: BLE001 - worker failures are asserted below
                owner_errors.append(err)

        monkeypatch.setattr(rules_module, "build_tag_rules", paused_build_tag_rules)
        owner = threading.Thread(target=build_rules)
        owner.start()
        assert started.wait(5)

        with pytest.raises(CitryLifecycleInProgress):
            app.register(TypedCard)

        release.set()
        owner.join(5)

        assert not owner.is_alive()
        assert owner_errors == []
        assert app._tag_rules_cache is not None
        assert "c-typed-card" not in app._tag_rules_cache

        app.register(TypedCard)
        assert app._tag_rules_cache is None
        assert "c-typed-card" in app._tag_rules()


class TestKwargsValidation:
    def test_unknown_attr_fails_at_parse(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card title="x" bogus="1"><c-fill name="header">H</c-fill></c-card>'

        with pytest.raises(SyntaxError, match="Found invalid attributes: bogus"):
            str(Page())

    def test_missing_required_kwarg_fails_at_parse(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="header">H</c-fill></c-card>'

        with pytest.raises(SyntaxError, match="must have one of the following attributes: 'title', 'c-title'"):
            str(Page())

    def test_all_required_kwargs_omitted_reports_first_declared_group(self):
        c = Citry()

        class TypedCard(Component):
            citry = c
            template = "<p>x</p>"

            class Kwargs:
                title: str
                subtitle: str

        class Page(Component):
            citry = c
            template = "<c-typed-card />"

        with pytest.raises(SyntaxError) as err:
            str(Page())

        # With every required kwarg missing, the parser reports the first
        # declared group's spellings alone rather than listing all missing
        # kwargs at once.
        msg = str(err.value)
        assert "Tag '<c-typed-card>' must have one of the following attributes: 'title', 'c-title'." in msg
        assert "subtitle" not in msg

    def test_error_names_next_missing_group_when_first_is_supplied(self):
        c = Citry()

        class TypedCard(Component):
            citry = c
            template = "<p>x</p>"

            class Kwargs:
                title: str
                subtitle: str

        class Page(Component):
            citry = c
            template = '<c-typed-card title="T" />'

        # Required groups are checked in declaration order, so satisfying
        # 'title' surfaces the next missing group.
        with pytest.raises(SyntaxError, match="must have one of the following attributes: 'subtitle', 'c-subtitle'"):
            str(Page())

    def test_dynamic_attr_form_accepted(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card c-title="t"><c-fill name="header">H</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"t": "T"}

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">TH</div>'

    @pytest.mark.parametrize(
        "attrs",
        [
            'title="static" c-title="dynamic"',
            'c-title="dynamic" title="static"',
        ],
    )
    def test_static_and_dynamic_same_kwarg_fails(self, attrs):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = f"""
                <c-card {attrs}><c-fill name="header">H</c-fill></c-card>
            """

        with pytest.raises(SyntaxError, match="must have only one of the attributes"):
            str(Page())

    def test_public_allowed_attr_groups_remain_mutually_exclusive(self):
        rules = {
            "c-card": TagRules(
                allowed_attrs=[["title", "c-title"]],
            )
        }

        with pytest.raises(SyntaxError, match="must have only one of the attributes"):
            parse_template(
                '<c-card title="static" c-title="dynamic" />',
                user_rules=rules,
            )

    def test_c_bind_bypasses_attr_checks(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card c-bind="props"><c-fill name="header">H</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"props": {"title": "T"}}

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">TH</div>'

    def test_control_flow_attrs_allowed(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card title="T" c-if="flag"><c-fill name="header">H</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"flag": True}

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">TH</div>'

    def test_optional_kwarg_can_be_omitted(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card title="T"><c-fill name="header">H</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">TH</div>'

    def test_empty_kwargs_class_rejects_all_attrs(self):
        # A component that takes no inputs declares an empty Kwargs class: its
        # empty field list means no attributes are allowed, unlike an
        # undeclared Kwargs which leaves the tag unrestricted.
        c = Citry()

        class Plain(Component):
            citry = c
            template = "<p>x</p>"

            class Kwargs:
                pass

        class Page(Component):
            citry = c
            template = '<c-plain title="T" />'

        with pytest.raises(SyntaxError, match="Found invalid attributes: title"):
            str(Page())

    def test_empty_kwargs_class_rejects_python_kwargs_at_render(self):
        # The same no-inputs declaration also guards the direct Python call.
        c = Citry()

        class Plain(Component):
            citry = c
            template = "<p>x</p>"

            class Kwargs:
                pass

        with pytest.raises(TypeError, match="got an unexpected keyword argument 'title'"):
            Plain(title="T").render()

    def test_empty_kwargs_class_allows_bare_use(self):
        c = Citry()

        class Plain(Component):
            citry = c
            template = "<p>x</p>"

            class Kwargs:
                pass

        class Page(Component):
            citry = c
            template = "<c-plain />"

        assert str(Page()) == '<p data-cid-c2="" data-cid-c1="">x</p>'


class TestSlotsValidation:
    def test_unknown_fill_fails_at_parse(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card title="T"><c-fill name="header">H</c-fill><c-fill name="bogus">B</c-fill></c-card>'

        with pytest.raises(SyntaxError, match="does not allow a slot named 'bogus'"):
            str(Page())

    def test_missing_required_slot_fails_at_parse(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card title="T"><c-fill name="footer">F</c-fill></c-card>'

        with pytest.raises(SyntaxError, match="must have a slot named 'header'"):
            str(Page())

    def test_implicit_default_content_rejected_when_not_declared(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card title="T">just text</c-card>'

        with pytest.raises(SyntaxError, match="does not allow a 'default' slot"):
            str(Page())

    def test_optional_slot_can_be_omitted(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card title="T"><c-fill name="header">H</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">TH</div>'

    def test_dynamic_fill_name_defers_per_name_checks(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-card title="T"><c-fill c-name="which">X</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"which": "header"}

        # A dynamic fill could resolve to the required name, so the per-name
        # check is deferred to runtime; this one does resolve to it.
        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">TX</div>'

    def test_unknown_typed_slot_data_source_fails_at_parent_parse(self):
        c = Citry()

        class RowSlotData:
            item: str
            index: int

        class Grid(Component):
            citry = c
            template = '<c-slot name="row" item="I" index="1" />'

            class Slots:
                row: SlotInput[RowSlotData]

        class Page(Component):
            citry = c
            template = """
              <c-grid>
                <c-fill name="row" data="{ missing }">
                  {{ missing }}
                </c-fill>
              </c-grid>
            """

        with pytest.raises(
            SyntaxError,
            match=r"does not expose a slot-data field named 'missing'.*Available fields: item, index",
        ):
            str(Page())

    def test_known_typed_slot_data_sources_render_with_alias_and_rest(self):
        c = Citry()

        class RowSlotData:
            item: str
            index: str

        class Grid(Component):
            citry = c
            template = '<c-slot name="row" item="I" index="1" />'

            class Slots:
                row: SlotInput[RowSlotData]

        class Page(Component):
            citry = c
            template = """
              <c-grid>
                <c-fill name="row" data="{ item as value, **rest }">
                  {{ value }}{{ rest.index }}
                </c-fill>
              </c-grid>
            """

        assert str(Page()).strip() == "I1"

    def test_dynamic_slot_name_keeps_missing_source_as_runtime_error(self):
        c = Citry()

        class RowSlotData:
            item: str

        class Grid(Component):
            citry = c
            template = '<c-slot name="row" item="I" />'

            class Slots:
                row: SlotInput[RowSlotData]

        class Page(Component):
            citry = c
            template = """
              <c-grid>
                <c-fill c-name="slot_name" data="{ missing }">
                  {{ missing }}
                </c-fill>
              </c-grid>
            """

            def template_data(self, kwargs, slots):
                return {"slot_name": "row"}

        with pytest.raises(RuntimeError, match="requested slot-data field 'missing'"):
            str(Page())


class TestValidationScope:
    def test_case_insensitive_tag_spelling(self):
        c = Citry()
        _declared_card(c)

        class Page(Component):
            citry = c
            template = '<c-Card title="T" bogus="1"><c-fill name="header">H</c-fill></c-Card>'

        with pytest.raises(SyntaxError, match="can only have the following attributes"):
            str(Page())

    def test_nested_template_attr_is_validated(self):
        c = Citry()
        _declared_card(c)

        class Holder(Component):
            citry = c
            template = "<div>{{ body }}</div>"

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

        class Page(Component):
            citry = c
            template = "<c-holder c-body=\"<c-card bogus='1' />\" />"

        with pytest.raises(SyntaxError, match="can only have the following attributes"):
            str(Page())

    def test_component_registered_after_parent_class_still_validated(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<c-late bogus="1" />'

        # `late` is declared AFTER Page's class definition but BEFORE Page's
        # first render; rules are built at parse time (first render), so the
        # declaration is seen.
        class Late(Component):
            citry = c
            template = "<p>x</p>"

            class Kwargs:
                title: str = "t"

        with pytest.raises(SyntaxError, match="can only have the following attributes"):
            str(Page())


# A stand-in following Pydantic's attribute protocol (v2: `model_fields` of
# infos with `is_required()`), so the duck-typed support is exercised without
# pydantic installed. The base class matters: like pydantic's BaseModel, it
# keeps the inner class from being auto-converted to a dataclass by the
# Component metaclass (which only converts plain `(object,)`-based classes).
class _FakeFieldInfo:
    def __init__(self, required):
        self._required = required

    def is_required(self):
        return self._required


class _FakeModelBase:
    model_fields: dict = {}

    def __init__(self, **data):
        for name in self.model_fields:
            setattr(self, name, data.get(name))


class TestFieldIntrospection:
    def test_get_fields_dataclass(self):
        from dataclasses import dataclass

        from citry.util.misc import FieldSpec, get_fields

        @dataclass
        class Kw:
            title: str
            size: int = 10

        assert get_fields(Kw) == [FieldSpec("title", required=True), FieldSpec("size", required=False)]

    def test_get_fields_namedtuple(self):
        from typing import NamedTuple

        from citry.util.misc import FieldSpec, get_fields

        class Kw(NamedTuple):
            title: str
            size: int = 10

        assert get_fields(Kw) == [FieldSpec("title", required=True), FieldSpec("size", required=False)]

    def test_get_fields_pydantic_v2_protocol(self):
        from citry.util.misc import FieldSpec, get_fields

        class Kw(_FakeModelBase):
            model_fields = {"title": _FakeFieldInfo(required=True), "size": _FakeFieldInfo(required=False)}

        assert get_fields(Kw) == [FieldSpec("title", required=True), FieldSpec("size", required=False)]

    def test_get_fields_pydantic_v1_protocol(self):
        from types import SimpleNamespace

        from citry.util.misc import FieldSpec, get_fields

        class Kw:
            __fields__ = {"title": SimpleNamespace(required=True), "size": SimpleNamespace(required=False)}

        assert get_fields(Kw) == [FieldSpec("title", required=True), FieldSpec("size", required=False)]

    def test_get_fields_unrecognized(self):
        from citry.util.misc import get_fields

        class Plain:
            title: str

        assert get_fields(None) is None
        assert get_fields(Plain) is None
        assert get_fields("not a class") is None

    def test_to_dict_pydantic_protocol_instance(self):
        from citry.util.misc import to_dict

        class Kw(_FakeModelBase):
            model_fields = {"title": _FakeFieldInfo(required=True)}

        assert to_dict(Kw(title="T")) == {"title": "T"}


class TestNonDataclassDeclarations:
    def test_namedtuple_kwargs_validated_and_render(self):
        from typing import NamedTuple

        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ title }}</p>"

            class Kwargs(NamedTuple):
                title: str
                size: int = 10

            def template_data(self, kwargs, slots):
                return {"title": kwargs.title}

        class Good(Component):
            citry = c
            template = '<c-card title="T" />'

        class Bad(Component):
            citry = c
            template = '<c-card title="T" bogus="1" />'

        assert str(Good()) == '<p data-cid-c2="" data-cid-c1="">T</p>'
        with pytest.raises(SyntaxError, match="can only have the following attributes"):
            str(Bad())

    def test_pydantic_protocol_kwargs_validated_and_render(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ title }}</p>"

            class Kwargs(_FakeModelBase):
                model_fields = {"title": _FakeFieldInfo(required=True)}

            def template_data(self, kwargs, slots):
                return {"title": kwargs.title}

        class Good(Component):
            citry = c
            template = '<c-card title="T" />'

        class Bad(Component):
            citry = c
            template = "<c-card />"

        assert str(Good()) == '<p data-cid-c2="" data-cid-c1="">T</p>'
        with pytest.raises(SyntaxError, match="must have one of the following attributes"):
            str(Bad())

    def test_real_pydantic_model(self):
        pydantic = pytest.importorskip("pydantic")

        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>{{ title }}</p>"

            class Kwargs(pydantic.BaseModel):
                title: str
                size: int = 10

            def template_data(self, kwargs, slots):
                return {"title": kwargs.title}

        class Bad(Component):
            citry = c
            template = '<c-card title="T" bogus="1" />'

        with pytest.raises(SyntaxError, match="can only have the following attributes"):
            str(Bad())
