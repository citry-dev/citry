"""
Tests for slot resolution at the ``<c-slot>`` site (docs/design/component_slots.md
section 5) and the ``on_slot_rendered`` extension hook (section 7).

With phase 4 in place, slots work end to end through templates alone: the
parent passes content with ``<c-fill>`` (or the implicit default body), and
the child's ``<c-slot>`` renders it, so several tests mirror the README's
slot examples verbatim.
"""

import pytest

from citry import Citry, Component, Extension, Slot


class TestFillOrFallback:
    def test_named_slot_renders_fill(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="header">FB</c-slot></div>'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="header">H</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">H</div>'

    def test_unfilled_slot_renders_fallback(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="header">FB</c-slot></div>'

        class Page(Component):
            citry = c
            template = "<c-card />"

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">FB</div>'

    def test_unfilled_empty_slot_renders_nothing(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="header" /></div>'

        class Page(Component):
            citry = c
            template = "<c-card />"

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1=""></div>'

    def test_explicit_empty_fill_suppresses_fallback(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="header">FB</c-slot></div>'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="header" /></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1=""></div>'

    def test_fallback_renders_in_child_scope(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<div><c-slot>Hi {{ who }}</c-slot></div>"

            def template_data(self, kwargs, slots):
                return {"who": "child"}

        class Page(Component):
            citry = c
            template = "<c-card />"

        # The fallback body renders as if the <c-slot> tags were not there,
        # i.e. against the child's own variables.
        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">Hi child</div>'

    def test_fill_renders_in_parent_scope(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="h">FB</c-slot></div>'

            def template_data(self, kwargs, slots):
                return {"who": "child"}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="h">Hi {{ who }}</c-fill></c-card>'

            def template_data(self, kwargs, slots):
                return {"who": "parent"}

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">Hi parent</div>'

    # A component whose slot sites sit inside <c-if>/<c-elif> branches keyed
    # on a kwarg. Resolution is render-time, so only the taken branch's site
    # looks up its fill or default; a fill aimed at a slot in an untaken
    # branch simply never renders, and is not an error.
    @pytest.mark.parametrize(
        ("branch", "filled", "expected"),
        [
            pytest.param(None, ("a", "b"), "", id="no-branch"),
            pytest.param("a", (), '<p id="a" data-cid-c2="" data-cid-c1="">Default A</p>', id="a-no-fills"),
            pytest.param("b", (), '<p id="b" data-cid-c2="" data-cid-c1="">Default B</p>', id="b-no-fills"),
            pytest.param("a", ("b",), '<p id="a" data-cid-c2="" data-cid-c1="">Default A</p>', id="a-fill-b"),
            pytest.param("b", ("b",), '<p id="b" data-cid-c2="" data-cid-c1="">Override B</p>', id="b-fill-b"),
            pytest.param("a", ("a", "b"), '<p id="a" data-cid-c2="" data-cid-c1="">Override A</p>', id="a-fill-both"),
            pytest.param("b", ("a", "b"), '<p id="b" data-cid-c2="" data-cid-c1="">Override B</p>', id="b-fill-both"),
        ],
    )
    def test_slots_in_conditional_branches(self, branch, filled, expected):
        c = Citry()

        class Cond(Component):
            citry = c
            template = (
                '<c-if cond="branch == \'a\'"><p id="a"><c-slot name="a">Default A</c-slot></p></c-if>'
                '<c-elif cond="branch == \'b\'"><p id="b"><c-slot name="b">Default B</c-slot></p></c-elif>'
            )

            def template_data(self, kwargs, slots):
                return {"branch": self.raw_kwargs.get("branch")}

        fill_tags = "".join(f'<c-fill name="{name}">Override {name.upper()}</c-fill>' for name in filled)
        branch_attr = f' branch="{branch}"' if branch else ""

        class Page(Component):
            citry = c
            template = f"<c-cond{branch_attr}>{fill_tags}</c-cond>"

        assert str(Page()) == expected


class TestDefaultSlot:
    def test_readme_button_example(self):
        c = Citry()

        class Button(Component):
            citry = c
            template = "<button><c-slot>Click me</c-slot></button>"

        class Bare(Component):
            citry = c
            template = "<c-button />"

        class Filled(Component):
            citry = c
            template = "<c-button>Submit</c-button>"

        # Usage without fill renders the fallback; with content, the fill.
        assert str(Bare()) == '<button data-cid-c2="" data-cid-c1="">Click me</button>'
        # The per-test id counter continues across renders: c3 is Filled, c4 its Button.
        assert str(Filled()) == '<button data-cid-c4="" data-cid-c3="">Submit</button>'

    def test_explicit_default_fill_targets_unnamed_slot(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<div><c-slot /></div>"

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="default">X</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">X</div>'

    def test_python_slots_fill_template_slots(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="header">FB</c-slot></div>'

        assert str(Card(slots={"header": "from python"})) == '<div data-cid-c1="">from python</div>'

    def test_implicit_body_is_ignored_without_a_default_slot_site(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>fixed</p>"

        class Page(Component):
            citry = c
            template = "<c-card>unused body</c-card>"

        assert str(Page()) == '<p data-cid-c2="" data-cid-c1="">fixed</p>'

    def test_implicit_body_is_ignored_when_default_slot_branch_is_not_taken(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<p><c-if cond="show"><c-slot /></c-if>fixed</p>'

            def template_data(self, kwargs, slots):
                return {"show": False}

        class Page(Component):
            citry = c
            template = "<c-card>unused body</c-card>"

        assert str(Page()) == '<p data-cid-c2="" data-cid-c1="">fixed</p>'


class TestRequiredSlot:
    def test_required_unfilled_raises(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="actions" required /></div>'

        with pytest.raises(RuntimeError, match="Slot 'actions' of component 'Card' is marked as required"):
            str(Card())

    def test_required_error_suggests_close_fill_name(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="header" required /></div>'

        with pytest.raises(RuntimeError, match="Did you mean 'headre'"):
            str(Card(slots={"headre": "typo"}))

    def test_required_filled_is_fine(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="actions" required>FB</c-slot></div>'

        assert str(Card(slots={"actions": "OK"})) == '<div data-cid-c1="">OK</div>'

    def test_required_in_untaken_branch_does_not_raise(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-if cond="flag"><c-slot name="actions" required /></c-if>no slot</div>'

            def template_data(self, kwargs, slots):
                return {"flag": False}

        # Resolution is render-time by design: a slot in an untaken branch
        # never renders, so it cannot complain.
        assert str(Card()) == '<div data-cid-c1="">no slot</div>'

    def test_dynamic_c_required(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="actions" c-required="strict" /></div>'

            def template_data(self, kwargs, slots):
                return {"strict": self.raw_kwargs.get("strict", False)}

        assert str(Card()) == '<div data-cid-c1=""></div>'
        with pytest.raises(RuntimeError, match="marked as required"):
            str(Card(strict=True))


class TestScopedSlotData:
    def test_slot_data_reaches_fill(self):
        c = Citry()

        class UserList(Component):
            citry = c
            template = '<ul><c-for each="u in users"><li><c-slot name="item" c-user="u" /></li></c-for></ul>'

            def template_data(self, kwargs, slots):
                return {"users": ["Ann", "Bob"]}

        class Page(Component):
            citry = c
            template = '<c-user-list><c-fill name="item" data="s">Hi {{ s["user"] }}</c-fill></c-user-list>'

        # The same fill renders once per slot site, each with that
        # iteration's data.
        assert str(Page()) == '<ul data-cid-c2="" data-cid-c1=""><li>Hi Ann</li><li>Hi Bob</li></ul>'

    def test_static_attrs_become_string_data(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="x" kind="static" /></div>'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="x" data="d">{{ d.kind }}</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">static</div>'

    def test_c_bind_spreads_slot_data_and_props(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot c-bind="props" /></div>'

            def template_data(self, kwargs, slots):
                return {"props": {"name": "item", "n": 42}}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="item" data="d">n={{ d.n }}</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">n=42</div>'

    @pytest.mark.parametrize(
        "slot_attrs",
        [
            'name="item" c-bind="props"',
            'c-bind="props" name="item"',
        ],
    )
    def test_c_bind_none_does_not_replace_static_slot_name(self, slot_attrs):
        c = Citry()

        class Card(Component):
            citry = c
            template = f"""
                <div><c-slot {slot_attrs}>FB</c-slot></div>
            """

            def template_data(self, kwargs, slots):
                return {"props": None}

        assert "FILLED" in str(Card(slots={"item": "FILLED"}))

    def test_c_bind_none_preserves_implicit_default_slot_name(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot c-bind="props">FB</c-slot></div>'

            def template_data(self, kwargs, slots):
                return {"props": None}

        assert "FILLED" in str(Card(slots={"default": "FILLED"}))

    def test_fill_without_data_opt_in_ignores_data(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="x" c-n="1" /></div>'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="x">plain</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">plain</div>'

    def test_dynamic_slot_name(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot c-name="which" /></div>'

            def template_data(self, kwargs, slots):
                return {"which": "header"}

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="header">H</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">H</div>'

    def test_dynamic_slot_names_inside_loop(self):
        c = Citry()

        class Sections(Component):
            citry = c
            template = '<c-for each="name in names"><c-slot c-name="name">{{ name }}</c-slot>|</c-for>'

            def template_data(self, kwargs, slots):
                return {"names": ["header", "main", "footer"]}

        class Page(Component):
            citry = c
            template = '<c-sections><c-fill name="header">H</c-fill><c-fill name="main">M</c-fill></c-sections>'

        assert str(Page()) == "H|M|footer|"


class TestFallbackAccess:
    def test_fill_can_wrap_fallback(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="title"><h1>Fallback Title</h1></c-slot></div>'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="title" fallback="fb"><b>[{{ fb }}]</b></c-fill></c-card>'

        # The README's "wrap the fallback with extra markup" example.
        assert str(Page()) == ('<div data-cid-c2="" data-cid-c1=""><b>[<h1>Fallback Title</h1>]</b></div>')

    def test_fallback_coerced_multiple_times(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="t">FB</c-slot></div>'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="t" fallback="fb">{{ fb }}+{{ fb }}</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">FB+FB</div>'

    def test_fallback_reevaluated_per_loop_iteration(self):
        c = Citry()

        class Loop(Component):
            citry = c
            template = (
                '<c-for each="obj in objects"><c-slot name="item" c-obj="obj">{{ obj }} default </c-slot></c-for>'
            )

            def template_data(self, kwargs, slots):
                return {"objects": self.raw_kwargs["objects"]}

        class Page(Component):
            citry = c
            # The outer fill receives each outer item via slot data and mounts
            # another Loop over that item's inner list; the inner fill renders
            # whatever fallback it was handed.
            template = (
                '<c-loop c-objects="objects">'
                '<c-fill name="item" data="d">'
                "<c-loop c-objects=\"d['obj']['inner']\">"
                '<c-fill name="item" fallback="fb">{{ fb }}</c-fill>'
                "</c-loop></c-fill></c-loop>"
            )

            def template_data(self, kwargs, slots):
                return {
                    "objects": [
                        {"inner": ["ITER1_OBJ1", "ITER1_OBJ2"]},
                        {"inner": ["ITER2_OBJ1", "ITER2_OBJ2"]},
                    ],
                }

        # The fill renders once per <c-slot> site inside the child's loop, and
        # the fallback binding is rebuilt each time, so every iteration hands
        # the fill its own fallback content ("<obj> default").
        assert str(Page()) == "ITER1_OBJ1 default ITER1_OBJ2 default ITER2_OBJ1 default ITER2_OBJ2 default "


class TestSlotComposition:
    def test_same_fill_renders_at_multiple_slot_sites(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot name="x" />|<c-slot name="x" /></div>'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="x">F</c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1="">F|F</div>'

    def test_unfilled_same_name_sites_keep_their_own_fallbacks(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<c-slot name="x">A</c-slot>|<c-slot name="x">B</c-slot>'

        assert str(Card()) == "A|B"

    def test_passthrough_slot(self):
        c = Citry()

        class Inner(Component):
            citry = c
            template = '<i><c-slot name="x">inner-fb</c-slot></i>'

        class Mid(Component):
            citry = c
            # Mid forwards its own "x" slot into Inner's "x" slot. The
            # <c-slot> inside the fill body resolves against MID's fills,
            # because the fill body closed over Mid's context.
            template = '<c-inner><c-fill name="x"><c-slot name="x">mid-fb</c-slot></c-fill></c-inner>'

        class Page(Component):
            citry = c
            template = '<c-mid><c-fill name="x">from page</c-fill></c-mid>'

        class PageNoFill(Component):
            citry = c
            template = "<c-mid />"

        assert str(Page()) == '<i data-cid-c3="" data-cid-c2="" data-cid-c1="">from page</i>'
        # Second render: c4 is PageNoFill, c5 Mid, c6 Inner.
        assert str(PageNoFill()) == '<i data-cid-c6="" data-cid-c5="" data-cid-c4="">mid-fb</i>'

    def test_fallback_through_passthrough_slot(self):
        c = Citry()

        class Inner(Component):
            citry = c
            template = '<i><c-slot name="x">inner-fb</c-slot></i>'

        class Mid(Component):
            citry = c
            template = '<c-inner><c-fill name="x"><c-slot name="x">mid-fb</c-slot></c-fill></c-inner>'

        class Page(Component):
            citry = c
            template = '<c-mid><c-fill name="x" fallback="fb">[{{ fb }}]</c-fill></c-mid>'

        # Page's fill targets Mid's slot, the one declared inside Mid's fill
        # to Inner, so the fallback binding delivers that site's default
        # ("mid-fb"), not the default of Inner's site where the content
        # finally lands.
        assert str(Page()) == '<i data-cid-c3="" data-cid-c2="" data-cid-c1="">[mid-fb]</i>'

    def test_dynamic_passthrough_ignores_unknown_fills(self):
        c = Citry()

        class Inner(Component):
            citry = c
            template = '<c-slot name="header">header-fb</c-slot>|<c-slot name="main">main-fb</c-slot>'

        class Forwarder(Component):
            citry = c
            template = (
                '<c-inner><c-for each="name in names">'
                '<c-fill c-name="name"><c-slot c-name="name" /></c-fill>'
                "</c-for></c-inner>"
            )

            def template_data(self, kwargs, slots):
                return {"names": list(self.raw_slots)}

        class Page(Component):
            citry = c
            template = (
                '<c-forwarder><c-fill name="header1">ignored</c-fill>'
                '<c-fill name="main">custom main</c-fill></c-forwarder>'
            )

        assert str(Page()) == "header-fb|custom main"

    def test_slot_inside_slot_fallback(self):
        c = Citry()

        class Card(Component):
            citry = c
            # The outer slot's fallback contains another slot.
            template = '<div><c-slot name="outer"><c-slot name="inner">deep-fb</c-slot></c-slot></div>'

        class PageFillsInner(Component):
            citry = c
            template = '<c-card><c-fill name="inner">I</c-fill></c-card>'

        class PageFillsOuter(Component):
            citry = c
            template = '<c-card><c-fill name="outer">O</c-fill></c-card>'

        # Filling only the inner slot renders the outer fallback with it;
        # filling the outer slot short-circuits the inner one entirely.
        assert str(PageFillsInner()) == '<div data-cid-c2="" data-cid-c1="">I</div>'
        # Second render: c3 is PageFillsOuter, c4 its Card.
        assert str(PageFillsOuter()) == '<div data-cid-c4="" data-cid-c3="">O</div>'

    def test_three_level_nested_slot_override_matrix(self):
        c = Citry()

        class Nested(Component):
            citry = c
            template = (
                '<c-slot name="outer">O[<c-slot name="middle">M[<c-slot name="inner">I</c-slot>]</c-slot>]</c-slot>'
            )

        class EmptyPage(Component):
            citry = c
            template = "<c-nested />"

        class OuterPage(Component):
            citry = c
            template = '<c-nested><c-fill name="outer">X</c-fill></c-nested>'

        class MiddlePage(Component):
            citry = c
            template = '<c-nested><c-fill name="middle">X</c-fill></c-nested>'

        class InnerPage(Component):
            citry = c
            template = '<c-nested><c-fill name="inner">X</c-fill></c-nested>'

        class AllPage(Component):
            citry = c
            template = (
                '<c-nested><c-fill name="inner">inner</c-fill>'
                '<c-fill name="middle">middle</c-fill>'
                '<c-fill name="outer">outer</c-fill></c-nested>'
            )

        assert str(EmptyPage()) == "O[M[I]]"
        assert str(OuterPage()) == "X"
        assert str(MiddlePage()) == "O[X]"
        assert str(InnerPage()) == "O[M[X]]"
        assert str(AllPage()) == "outer"

    def test_component_inside_fill_rendered_at_slot_site(self):
        c = Citry()

        class Icon(Component):
            citry = c
            template = "<svg>icon</svg>"

        class Card(Component):
            citry = c
            template = '<div><c-slot name="x" /></div>'

        class Page(Component):
            citry = c
            template = '<c-card><c-fill name="x"><c-icon /></c-fill></c-card>'

        assert str(Page()) == '<div data-cid-c2="" data-cid-c1=""><svg data-cid-c3="">icon</svg></div>'


class TestOnSlotRenderedHook:
    def test_hook_observes_slot_renders(self):
        seen = []

        class Spy(Extension):
            name = "spy"

            def on_slot_rendered(self, ctx):
                seen.append((type(ctx.component).__name__, ctx.slot_name, ctx.slot_is_required, str(ctx.result)))

        c = Citry(extensions=[Spy])

        class Card(Component):
            citry = c
            template = '<div><c-slot name="h">FB</c-slot></div>'

        str(Card(slots={"h": "H"}))
        str(Card())
        assert seen == [("Card", "h", False, "H"), ("Card", "h", False, "FB")]

    def test_hook_replaces_result(self):
        class Upper(Extension):
            name = "upper"

            def on_slot_rendered(self, ctx):
                return str(ctx.result).upper()

        c = Citry(extensions=[Upper])

        class Card(Component):
            citry = c
            template = '<div><c-slot name="h">fb</c-slot></div>'

        assert str(Card(slots={"h": "hi"})) == '<div data-cid-c1="">HI</div>'

    def test_hook_raise_propagates(self):
        class Boom(Extension):
            name = "boom"

            def on_slot_rendered(self, ctx):
                msg = "no slots today"
                raise ValueError(msg)

        c = Citry(extensions=[Boom])

        class Card(Component):
            citry = c
            template = "<div><c-slot /></div>"

        with pytest.raises(ValueError, match="no slots today"):
            str(Card())

    def test_hook_sees_fill_slot_vs_fallback_slot(self):
        kinds = []

        class Spy(Extension):
            name = "spy"

            def on_slot_rendered(self, ctx):
                kinds.append(isinstance(ctx.slot, Slot))

        c = Citry(extensions=[Spy])

        class Card(Component):
            citry = c
            template = '<div><c-slot name="h">FB</c-slot></div>'

        str(Card(slots={"h": "H"}))
        str(Card())
        # Both paths hand the hook a Slot: the fill, or the fallback wrapper.
        assert kinds == [True, True]


class TestSlotErrors:
    def test_boolean_name_is_rejected_during_parse(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<div><c-slot name /></div>"

        with pytest.raises(SyntaxError, match="static 'name' must have a non-empty value"):
            str(Card())

    def test_c_bind_must_be_mapping(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = '<div><c-slot c-bind="props" /></div>'

            def template_data(self, kwargs, slots):
                return {"props": ["not", "a", "mapping"]}

        with pytest.raises(RuntimeError, match="must resolve to a mapping"):
            str(Card())

    def test_c_bind_must_use_string_keys(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = """
                <div><c-slot c-bind="props" /></div>
            """

            def template_data(self, kwargs, slots):
                return {"props": {1: "value"}}

        with pytest.raises(TypeError, match=r"c-bind' on <c-slot> must use string keys"):
            str(Card())
