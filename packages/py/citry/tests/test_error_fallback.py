"""
Tests for the ``<c-error-fallback>`` built-in component
(docs/design/component_on_render.md section 7): an error boundary that catches render
errors in its guarded content (the default slot) and shows the ``fallback``
attribute or the ``fallback`` fill instead.
"""

import pytest

from citry import AlreadyRegistered, Citry, Component


def _make_failing(c):
    class Failing(Component):
        citry = c
        template = "<i>x</i>"

        def template_data(self, kwargs, slots):
            raise ValueError("boom")

    return Failing


class TestErrorFallback:
    def test_no_error_renders_content(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<main><c-error-fallback fallback="Oops"><b>all good</b></c-error-fallback></main>'

        html = Page().render().serialize()
        assert ">all good</b>" in html
        assert "Oops" not in html

    def test_fallback_fill_suppressed_when_content_is_safe(self):
        # The fill form of the fallback also stays unrendered when the guarded
        # content renders fine (the attribute form is locked above).
        c = Citry()

        class Page(Component):
            citry = c
            template = (
                '<main><c-error-fallback><c-fill name="default">SAFE</c-fill>'
                '<c-fill name="fallback">FB</c-fill></c-error-fallback></main>'
            )

        assert Page().render().serialize() == '<main data-cid-c1="">SAFE</main>'

    def test_fallback_attribute_on_child_component_error(self):
        c = Citry()
        _make_failing(c)

        class Page(Component):
            citry = c
            template = '<main><c-error-fallback fallback="Oops"><c-failing /></c-error-fallback></main>'

        html = Page().render().serialize()
        assert "Oops" in html
        assert "<i>" not in html

    def test_fallback_attribute_on_synchronous_content_error(self):
        # The guarded content renders inside the boundary's own body walk; a
        # plain expression error there is caught too.
        c = Citry()

        class Page(Component):
            citry = c
            template = '<main><c-error-fallback fallback="Oops"><b>{{ broken() }}</b></c-error-fallback></main>'

            def template_data(self, kwargs, slots):
                def boom():
                    raise ValueError("sync boom")

                return {"broken": boom}

        html = Page().render().serialize()
        assert "Oops" in html

    def test_fallback_slot_receives_error_as_data(self):
        c = Citry()
        _make_failing(c)

        class Page(Component):
            citry = c
            template = (
                "<main><c-error-fallback>"
                '<c-fill name="default"><c-failing /></c-fill>'
                '<c-fill name="fallback" data="d"><p>Caught: {{ d.error }}</p></c-fill>'
                "</c-error-fallback></main>"
            )

        html = Page().render().serialize()
        assert ">Caught: " in html
        assert "boom" in html

    def test_fallback_slot_from_python_gets_error_object(self):
        caught = []
        c = Citry()
        failing = _make_failing(c)
        error_fallback = c.get("error-fallback")

        def fallback(ctx):
            caught.append(ctx.data.error)
            return "recovered"

        html = (
            error_fallback(
                slots={"default": lambda _ctx: failing(), "fallback": fallback},
            )
            .render()
            .serialize()
        )

        assert "recovered" in html
        assert isinstance(caught[0], ValueError)

    def test_fallback_kwarg_from_python(self):
        # Same contract as the template's fallback attribute, entered from
        # Python: content when the default slot renders, fallback when it raises.
        c = Citry()
        failing = _make_failing(c)
        error_fallback = c.get("error-fallback")

        ok = error_fallback(fallback="FB", slots={"default": lambda _ctx: "SAFE"}).render().serialize()
        assert ok == "SAFE"

        caught = error_fallback(fallback="FB", slots={"default": lambda _ctx: failing()}).render().serialize()
        assert caught == "FB"

    def test_fallback_slot_suppressed_from_python_when_content_is_safe(self):
        # The slot form of the fallback stays unrendered on the Python path
        # when the default slot renders fine.
        c = Citry()
        error_fallback = c.get("error-fallback")

        slots = {"default": lambda _ctx: "SAFE", "fallback": lambda _ctx: "FB"}
        assert error_fallback(slots=slots).render().serialize() == "SAFE"

    def test_no_fallback_from_python_renders_empty_on_error(self):
        c = Citry()
        failing = _make_failing(c)
        error_fallback = c.get("error-fallback")

        html = error_fallback(slots={"default": lambda _ctx: failing()}).render().serialize()
        assert html == ""

    def test_fallback_slot_only_from_python_renders_empty(self):
        c = Citry()
        error_fallback = c.get("error-fallback")

        html = error_fallback(slots={"fallback": lambda _ctx: "FB"}).render().serialize()
        assert html == ""

    def test_attribute_and_slot_together_raise(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = (
                '<main><c-error-fallback fallback="x">'
                '<c-fill name="default"><i>y</i></c-fill>'
                '<c-fill name="fallback">z</c-fill>'
                "</c-error-fallback></main>"
            )

        with pytest.raises(RuntimeError, match="give only one"):
            Page().render()

    def test_no_fallback_renders_nothing_on_error(self):
        c = Citry()
        _make_failing(c)

        class Page(Component):
            citry = c
            template = "<main>before<c-error-fallback><c-failing /></c-error-fallback>after</main>"

        html = Page().render().serialize()
        assert "before" in html
        assert "after" in html
        assert "<i>" not in html

    def test_fallback_attribute_without_content_renders_nothing(self):
        # A fallback with no guarded content has nothing to fail, so nothing
        # shows.
        c = Citry()

        class Page(Component):
            citry = c
            template = '<main><c-error-fallback fallback="FB"></c-error-fallback></main>'

        html = Page().render().serialize()
        assert html == '<main data-cid-c1=""></main>'

    def test_fallback_fill_without_content_renders_nothing(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<main><c-error-fallback><c-fill name="fallback">FB</c-fill></c-error-fallback></main>'

        html = Page().render().serialize()
        assert html == '<main data-cid-c1=""></main>'

    def test_rest_of_page_renders_around_caught_error(self):
        c = Citry()
        _make_failing(c)

        class Aside(Component):
            citry = c
            template = "<aside>untouched</aside>"

        class Page(Component):
            citry = c
            template = '<main><c-error-fallback fallback="Oops"><c-failing /></c-error-fallback><c-aside /></main>'

        html = Page().render().serialize()
        assert "Oops" in html
        assert ">untouched</aside>" in html

    def test_boundaries_inside_loop_catch_independently(self):
        # One boundary per <c-for> iteration: failing iterations show their
        # fallback (which can read the loop variable), succeeding ones render
        # normally, in source order.
        c = Citry()

        class Sometimes(Component):
            citry = c
            template = "Item: {{ name }}"

            def template_data(self, kwargs, slots):
                if kwargs["broken"]:
                    raise ValueError("loop boom")
                return {"name": kwargs["name"]}

        class Page(Component):
            citry = c
            template = (
                '<div><c-for each="item in items">'
                "<c-error-fallback>"
                '<c-fill name="default"><c-sometimes c-name="item[\'name\']" c-broken="item[\'broken\']" /></c-fill>'
                "<c-fill name=\"fallback\">ERROR: {{ item['name'] }}</c-fill>"
                "</c-error-fallback> "
                "</c-for></div>"
            )

            def template_data(self, kwargs, slots):
                return {
                    "items": [
                        {"name": "i1", "broken": False},
                        {"name": "i2", "broken": True},
                        {"name": "i3", "broken": False},
                        {"name": "i4", "broken": True},
                    ],
                }

        html = Page().render().serialize()
        assert html == '<div data-cid-c1="">Item: i1 ERROR: i2 Item: i3 ERROR: i4 </div>'

    def test_nested_boundaries_inner_wins(self):
        c = Citry()
        _make_failing(c)

        class Page(Component):
            citry = c
            template = (
                '<main><c-error-fallback fallback="outer">'
                '<c-error-fallback fallback="inner"><c-failing /></c-error-fallback>'
                "</c-error-fallback></main>"
            )

        html = Page().render().serialize()
        assert "inner" in html
        assert "outer" not in html

    def test_failing_fallback_bubbles_to_outer_boundary(self):
        c = Citry()
        _make_failing(c)

        class Inner(Component):
            citry = c
            template = (
                "<c-error-fallback>"
                '<c-fill name="default"><c-failing /></c-fill>'
                '<c-fill name="fallback">{{ also_broken() }}</c-fill>'
                "</c-error-fallback>"
            )

            def template_data(self, kwargs, slots):
                def boom2():
                    raise ValueError("fallback boom")

                return {"also_broken": boom2}

        class Page(Component):
            citry = c
            template = '<main><c-error-fallback fallback="outer caught"><c-inner /></c-error-fallback></main>'

        html = Page().render().serialize()
        assert "outer caught" in html

    def test_escaped_error_names_guarded_child(self):
        # The same failing child in both shapes: guarded, the boundary
        # swallows the error and the page renders; bare, the error escapes
        # with a path naming the failing component.
        c = Citry()
        _make_failing(c)

        class Page(Component):
            citry = c
            template = "<main><c-error-fallback><c-failing /></c-error-fallback></main>"

        class Bare(Component):
            citry = c
            template = "<main><c-failing /></main>"

        assert Page().render().serialize() == '<main data-cid-c1=""></main>'

        with pytest.raises(ValueError, match="boom") as exc_info:
            Bare().render()

        assert "Bare > Failing" in exc_info.value.args[0]

    def test_unexpected_kwargs_rejected(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<main><c-error-fallback bogus="x"><b>y</b></c-error-fallback></main>'

        with pytest.raises(Exception, match="bogus"):
            Page().render()

    def test_name_is_reserved(self):
        c = Citry()

        with pytest.raises(AlreadyRegistered, match="error-fallback"):

            class ErrorFallback(Component):
                citry = c
                template = "<p>impostor</p>"
