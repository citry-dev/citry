"""
Tests for the ``Component.on_render`` hook (docs/design/component_on_render.md
sections 3-4). Plain form: returning ``None`` renders the template as usual;
returning content (``str`` / composed element / ``CitryRender`` / ``Slot``)
replaces the component's whole output and the template is never rendered. A
plain ``str`` is escaped text and ``Markup`` is HTML, as in ``{{ ... }}``.
Generator form: code before the first yield runs before the template renders,
each yield receives the settled ``(result, error)``, and the generator may
replace the output, catch a child's error, or raise.
"""

import json
import re
import warnings

import pytest

from citry import Citry, CitryRender, Component, Extension, Markup
from citry._vue.capture import render_prepared_direct
from citry._vue.direct_capture import assemble_typed_render
from citry.citry_render import DeferredComponent
from citry.ext.debug import Debug


def _has_deferred(render):
    """True if any DeferredComponent part remains anywhere in the render."""

    def walk(parts):
        for part in parts:
            if isinstance(part, DeferredComponent):
                return True
            if isinstance(part, CitryRender) and walk(part.parts):
                return True
        return False

    return walk(render.parts)


def _assemble_prepared(component):
    return assemble_typed_render(
        render_prepared_direct(component),
        revision=0,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )


class TestOnRenderPlainForm:
    def test_default_renders_template(self):
        c = Citry()

        class Plain(Component):
            citry = c
            template = "<p>template</p>"

        assert ">template</p>" in Plain().render().serialize()

    def test_none_renders_template(self):
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>template</p>"

            def on_render(self):
                return None

        assert ">template</p>" in Comp().render().serialize()

    def test_str_replaces_output_and_skips_template(self):
        rendered_data = []
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>{{ tracked() }}</p>"

            def template_data(self, kwargs, slots):
                def tracked():
                    rendered_data.append("template rendered")
                    return "x"

                return {"tracked": tracked}

            def on_render(self):
                return Markup("<b>replaced</b>")

        html = Comp().render().serialize()
        assert ">replaced</b>" in html
        assert "<p>" not in html
        # The template body was never walked.
        assert rendered_data == []

    def test_plain_str_is_escaped_as_text(self):
        # A plain str is text, as in a {{ ... }} expression, so user input
        # returned from the hook cannot inject a script.
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                return '<script>let a = "1";</script> & more'

        html = Comp().render().serialize()
        assert html == "&lt;script&gt;let a = &#34;1&#34;;&lt;/script&gt; &amp; more"

    def test_markup_is_inserted_as_html(self):
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                return Markup('<script>let a = "1";</script>')

        html = Comp().render().serialize()
        assert html == '<script data-cid-c1="">let a = "1";</script>'

    def test_html_protocol_object_is_inserted_as_html(self):
        # Any object with __html__ is trusted HTML, the same as in {{ ... }}.
        c = Citry()

        class Trusted:
            def __html__(self):
                return "<em>trusted</em>"

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                return Trusted()

        assert Comp().render().serialize() == '<em data-cid-c1="">trusted</em>'

    def test_empty_str_means_empty_output(self):
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                return ""

        assert Comp().render().serialize() == ""

    def test_element_replacement_renders_in_place(self):
        c = Citry()

        class Other(Component):
            citry = c
            template = "<i>{{ name }}</i>"

            class Kwargs:
                name: str

            def template_data(self, kwargs, slots):
                return {"name": kwargs.name}

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                return Other(name="delegated")

        html = Comp().render().serialize()
        assert ">delegated</i>" in html
        assert "<p>" not in html

    def test_element_replacement_with_nested_children(self):
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<em>inner</em>"

        class Outer(Component):
            citry = c
            template = "<div><c-inner /></div>"

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                return Outer()

        html = Comp().render().serialize()
        assert ">inner</em>" in html

    def test_element_replacement_sets_parent_link(self):
        seen = []
        c = Citry()

        class Other(Component):
            citry = c
            template = "<i>x</i>"

            def template_data(self, kwargs, slots):
                seen.append(type(self.parent).__name__ if self.parent else None)

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                return Other()

        Comp().render()
        assert seen == ["Comp"]

    def test_citry_render_replacement_is_inlined(self):
        c = Citry()

        class Other(Component):
            citry = c
            template = "<i>prerendered</i>"

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                return Other().render()

        html = Comp().render().serialize()
        assert ">prerendered</i>" in html

    def test_slot_replacement_renders_fill(self):
        # Slot semantics apply unchanged: a plain-string fill is text (it is
        # escaped when the slot is invoked).
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                return self.raw_slots["body"]

        html = Comp(slots={"body": "from <slot>"}).render().serialize()
        assert "from &lt;slot&gt;" in html
        assert "<p>" not in html

    def test_unsupported_type_raises_type_error(self):
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                return 42

        with pytest.raises(TypeError, match=r"Comp\.on_render"):
            Comp().render()

    def test_component_without_template(self):
        # The hook fires for template-less components too; without a
        # replacement, the output is empty.
        c = Citry()

        class NoTemplate(Component):
            citry = c

            def on_render(self):
                return Markup("<p>made up</p>")

        assert str(NoTemplate()) == '<p data-cid-c1="">made up</p>'

    def test_works_for_nested_components(self):
        c = Citry()

        class Leaf(Component):
            citry = c
            template = "<i>leaf</i>"

            def on_render(self):
                return Markup("<i>hooked</i>")

        class Root(Component):
            citry = c
            template = "<main><c-leaf /></main>"

        html = Root().render().serialize()
        assert ">hooked</i>" in html
        assert "leaf" not in html

    def test_transparent_component_gets_no_marker(self):
        c = Citry()

        class Glass(Component):
            citry = c
            transparent = True
            template = "<p>x</p>"

            def on_render(self):
                return Markup("<p>see-through</p>")

        class Root(Component):
            citry = c
            template = "<main><c-glass /></main>"

        html = Root().render().serialize()
        assert "<p>see-through</p>" in html

    def test_error_in_hook_carries_component_path(self):
        c = Citry()

        class Leaf(Component):
            citry = c
            template = "<i>x</i>"

            def on_render(self):
                raise ValueError("boom")

        class Root(Component):
            citry = c
            template = "<main><c-leaf /></main>"

        with pytest.raises(ValueError, match="boom") as exc_info:
            Root().render()

        assert exc_info.value.args[0].startswith(
            "An error occurred while rendering components Root > Leaf:\n",
        )


class TestOnRenderGeneratorForm:
    """
    The generator form (docs/design/component_on_render.md section 3.2): code before the
    first yield runs before the template renders; the yield receives the
    component's settled ``(result, error)``; the generator may replace the
    output (any number of times), raise, or keep the result.
    """

    def test_before_phase_runs_before_template(self):
        order = []
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>{{ tracked() }}</p>"

            def template_data(self, kwargs, slots):
                def tracked():
                    order.append("template")
                    return "x"

                return {"tracked": tracked}

            def on_render(self):
                order.append("before")
                yield

        Comp().render()
        assert order == ["before", "template"]

    def test_bare_yield_receives_settled_render(self):
        received = []
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<em>inner</em>"

        class Comp(Component):
            citry = c
            template = "<div><c-inner /></div>"

            def on_render(self):
                result, error = yield
                received.append((result, error))

        html = Comp().render().serialize()
        assert ">inner</em>" in html

        (result, error) = received[0]
        assert error is None
        assert isinstance(result, CitryRender)
        # The subtree is settled: no DeferredComponent parts remain anywhere.
        assert not _has_deferred(result)

    def test_first_yield_content_replaces_template(self):
        received = []
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>template</p>"

            def on_render(self):
                result, error = yield Markup("<b>yielded</b>")
                received.append((result, error))

        html = Comp().render().serialize()
        assert ">yielded</b>" in html
        assert "template" not in html
        assert received[0][1] is None

    def test_return_after_yield_replaces_output(self):
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>template</p>"

            def on_render(self):
                _result, _error = yield
                return Markup("<b>final</b>")

        html = Comp().render().serialize()
        assert ">final</b>" in html
        assert "template" not in html

    def test_yielded_and_returned_plain_str_is_escaped(self):
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                result, _error = yield "<b>first</b>"
                assert "&lt;b&gt;first&lt;/b&gt;" in result.serialize()
                return "<i>final</i>"

        assert Comp().render().serialize() == "&lt;i&gt;final&lt;/i&gt;"

    def test_plain_return_keeps_output(self):
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>kept</p>"

            def on_render(self):
                _result, _error = yield

        assert ">kept</p>" in Comp().render().serialize()

    def test_component_without_template_yield_receives_empty_render(self):
        # A template-less component still settles: the yield receives an
        # empty CitryRender (not None), and without a replacement the
        # component's output stays empty.
        received = []
        c = Citry()

        class NoTemplate(Component):
            citry = c

            def on_render(self):
                result, error = yield
                received.append((result, error))

        assert NoTemplate().render().serialize() == ""

        (result, error) = received[0]
        assert error is None
        assert isinstance(result, CitryRender)
        assert result.serialize() == ""
        assert not _has_deferred(result)

    def test_component_without_template_return_replaces_empty_output(self):
        c = Citry()

        class NoTemplate(Component):
            citry = c

            def on_render(self):
                _result, _error = yield
                return Markup("<p>made up</p>")

        assert NoTemplate().render().serialize() == '<p data-cid-c1="">made up</p>'

    def test_raise_after_yield_becomes_component_error(self):
        c = Citry()

        class Leaf(Component):
            citry = c
            template = "<i>x</i>"

            def on_render(self):
                _result, _error = yield
                raise ValueError("post-yield boom")

        class Root(Component):
            citry = c
            template = "<main><c-leaf /></main>"

        with pytest.raises(ValueError, match="post-yield boom") as exc_info:
            Root().render()

        assert exc_info.value.args[0].startswith(
            "An error occurred while rendering components Root > Leaf:\n",
        )

    def test_error_boundary_catches_child_error(self):
        # The ErrorFallback pattern: a failing child's error is delivered to
        # the enclosing generator, which swallows it with fallback output.
        c = Citry()

        class Failing(Component):
            citry = c
            template = "<i>x</i>"

            def template_data(self, kwargs, slots):
                raise ValueError("boom")

        class Guard(Component):
            citry = c
            template = "<div><c-failing /></div>"

            def on_render(self):
                _result, error = yield
                if error is not None:
                    return Markup("<p>fallback</p>")
                return None

        class Root(Component):
            citry = c
            template = "<main><c-guard /></main>"

        html = Root().render().serialize()
        assert ">fallback</p>" in html

    def test_unhandled_error_keeps_bubbling_past_generator(self):
        # A generator that returns None on error does not swallow it.
        seen = []
        c = Citry()

        class Failing(Component):
            citry = c
            template = "<i>x</i>"

            def template_data(self, kwargs, slots):
                raise ValueError("boom")

        class Observer(Component):
            citry = c
            template = "<div><c-failing /></div>"

            def on_render(self):
                _result, error = yield
                seen.append(error)

        with pytest.raises(ValueError, match="boom"):
            Observer().render()

        assert len(seen) == 1
        assert isinstance(seen[0], ValueError)

    def test_multiple_yields_each_receive_settled_result(self):
        received = []
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>original</p>"

            def on_render(self):
                result_a, _ = yield
                received.append(result_a.serialize())
                result_b, _ = yield Markup("<b>second</b>")
                received.append(result_b.serialize())
                return Markup("<u>third</u>")

        html = Comp().render().serialize()
        assert ">third</u>" in html
        assert ">original</p>" in received[0]
        assert ">second</b>" in received[1]

    def test_bare_yield_after_first_peeks_unchanged_result(self):
        received = []
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>once</p>"

            def on_render(self):
                result_a, _ = yield
                result_b, _ = yield None
                received.append(result_a is result_b)

        Comp().render()
        assert received == [True]

    def test_yielded_element_with_children_settles_before_resume(self):
        received = []
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<em>inner</em>"

        class Replacement(Component):
            citry = c
            template = "<div><c-inner /></div>"

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                result, error = yield Replacement()
                received.append((result, error))

        html = Comp().render().serialize()
        assert ">inner</em>" in html

        result, error = received[0]
        assert error is None
        assert not _has_deferred(result)

    def test_error_in_yielded_content_returns_to_same_generator(self):
        # An error inside content the generator yielded comes back to the
        # same generator, which can recover.
        c = Citry()

        class Failing(Component):
            citry = c
            template = "<i>x</i>"

            def template_data(self, kwargs, slots):
                raise ValueError("boom")

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                _result, error = yield Failing()
                if error is not None:
                    return Markup("<p>recovered</p>")
                return None

        html = Comp().render().serialize()
        assert ">recovered</p>" in html

    def test_unrenderable_yield_returns_to_same_generator(self):
        received = []
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>x</p>"

            def on_render(self):
                _result, error = yield 42
                received.append(error)
                return Markup("<p>recovered</p>")

        html = Comp().render().serialize()
        assert ">recovered</p>" in html
        assert isinstance(received[0], TypeError)

    def test_generator_returning_before_yield_acts_like_plain_form(self):
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>template</p>"

            def on_render(self):
                if True:
                    return Markup("<b>early</b>")
                yield  # makes this a generator function

        html = Comp().render().serialize()
        assert ">early</b>" in html
        assert "template" not in html

    def test_extension_hook_runs_after_generator_settles(self):
        seen = []

        class Recorder(Extension):
            name = "recorder"

            def on_component_rendered(self, ctx):
                if ctx.render is not None:
                    seen.append(ctx.render.serialize())

        c = Citry(extensions=[Recorder])

        class Comp(Component):
            citry = c
            template = "<p>original</p>"

            def on_render(self):
                yield
                return Markup("<b>final</b>")

        Comp().render()
        # The extension sees only the generator's final output, once.
        assert len(seen) == 1
        assert ">final</b>" in seen[0]

    @pytest.mark.qualification
    def test_deep_generator_chain_does_not_recurse(self):
        # A generator at every level of a deep tree; the drive loop keeps
        # depth flat, so this stays well past Python's recursion limit.
        c = Citry()
        depth = 600

        class Leaf(Component):
            citry = c
            template = "<i>bottom</i>"

        def make_on_render():
            def on_render(self):
                _result, _error = yield

            return on_render

        prev_tag = "leaf"
        top: type[Component] = Leaf
        for i in range(depth):
            # type() with the proper name, so each class registers uniquely.
            top = type(
                f"Level{i}",
                (Component,),
                {
                    "citry": c,
                    "template": f"<div><c-{prev_tag} /></div>",
                    "on_render": make_on_render(),
                },
            )
            prev_tag = f"level{i}"

        html = top().render().serialize()
        assert ">bottom</i>" in html

    def test_hook_order_across_a_tree_with_siblings(self):
        # The cross-component ordering guarantee behind djc's three-hook
        # "order" test: a parent's pre-yield phase runs before its children's
        # hooks, each child settles completely (post phase included) before
        # the next sibling starts, and the parent's post phase runs last.
        c = Citry()
        events = []

        def make(name, tpl):
            def on_render(self):
                events.append(f"{name}:pre")
                yield  # the settled result is not needed, only the phase order
                events.append(f"{name}:post")

            return type(name, (Component,), {"citry": c, "template": tpl, "on_render": on_render})

        make("Leaf1", "<i>1</i>")
        make("Leaf2", "<i>2</i>")
        make("Mid", "<div><c-leaf1 /><c-leaf2 /></div>")
        root = make("Root", "<main><c-mid /></main>")

        str(root())
        assert events == [
            "Root:pre",
            "Mid:pre",
            "Leaf1:pre",
            "Leaf1:post",
            "Leaf2:pre",
            "Leaf2:post",
            "Mid:post",
            "Root:post",
        ]

    def test_prepared_generator_slot_calls_keep_receiver_on_prime_and_resume(self):
        c = Citry(autodiscover=False)
        phases = []

        class Boundary(Component):
            citry = c

            def on_render(self):
                phases.append("prime")
                first = self.raw_slots["default"]({"label": "prime"})
                _result, error = yield first
                assert error is None
                phases.append("resume")
                return self.raw_slots["default"]({"label": "resume"})

        class Page(Component):
            citry = c
            template = '<c-Boundary><c-fill name="default" data="d"><b>{{ d.label }}</b></c-fill></c-Boundary>'

        assembly = _assemble_prepared(Page())

        assert phases == ["prime", "resume"]
        assert len(assembly.view.occurrences) == 2
        root = next(item for item in assembly.view.occurrences if item.id == assembly.view.root_id)
        assert root.prepared_data["citryText0"] == "resume"
        assert "prime" not in root.prepared_data.values()


class TestOnRenderInteractivePage:
    """
    A returned value follows the same text-or-HTML rule on a page that runs
    Vue: a plain str reaches the browser as a text node with the same text
    the server sent, and Markup stays HTML.
    """

    USER_INPUT = "<script>alert(1)</script> & <b>bold</b>"

    def _page(self, value, *, document):
        app = Citry(autodiscover=False)

        class Replaced(Component):
            citry = app
            template = "<p>unused</p>"

            def on_render(self):
                result, _error = yield
                assert result is not None
                return value

        class Counter(Component):
            citry = app
            template = '<button @click="count += 1">{{ count }}</button>'

            def template_data(self, kwargs, slots):
                return {"count": 0}

        body = "<c-Replaced /><c-Counter />"
        if document:
            template = f"<!doctype html><html><head></head><body>{body}</body></html>"
        else:
            template = f"<div>{body}</div>"

        class Page(Component):
            citry = app

        Page.template = template
        return Page

    @pytest.mark.parametrize("document", [True, False], ids=["document", "fragment"])
    def test_plain_str_is_escaped(self, document):
        # A full page used to raise "interactive document shell received
        # unsupported typed part str" here.
        html = str(self._page(self.USER_INPUT, document=document)())
        assert "&lt;script&gt;alert(1)&lt;/script&gt; &amp; &lt;b&gt;bold&lt;/b&gt;" in html
        assert "<script>alert(1)" not in html
        assert "<b>bold</b>" not in html

    @pytest.mark.parametrize("document", [True, False], ids=["document", "fragment"])
    def test_markup_is_inserted_as_html(self, document):
        html = str(self._page(Markup("<b>bold</b>"), document=document)())
        assert "<b>bold</b>" in html

    def test_plain_str_reaches_vue_as_text_data(self):
        # The browser renders the text from the same value the server
        # escaped, so hydration sees identical text on both sides.
        app = Citry(autodiscover=False)

        class Replaced(Component):
            citry = app
            template = "<p>unused</p>"

            def on_render(self):
                return "<b>bold</b>"

        assembly = _assemble_prepared(Replaced())
        [occurrence] = assembly.view.occurrences
        # Vue renders a text interpolation (never v-html) of the raw value.
        assert assembly.compile_inputs[occurrence.definition_id].template == "{{ $citryPrepared.citryText0 }}"
        assert occurrence.prepared_data["citryText0"] == "<b>bold</b>"

    def test_markup_reaches_vue_as_trusted_html(self):
        # Server events render through the Vue target, which takes HTML only
        # as a typed part; returned Markup must not be rejected there.
        app = Citry(autodiscover=False)

        class Replaced(Component):
            citry = app
            template = "<p>unused</p>"

            def on_render(self):
                return Markup("<s>x</s>")

        assembly = _assemble_prepared(Replaced())
        [occurrence] = assembly.view.occurrences
        template = assembly.compile_inputs[occurrence.definition_id].template
        assert template == '<citry-opaque-html :record="$citryPrepared.opaqueHtml.citryOpaque0"></citry-opaque-html>'
        assert occurrence.prepared_data["opaqueHtml"] == {"citryOpaque0": {"html": "<s>x</s>", "nodeCount": 1}}


def _named_cids(html: str) -> str:
    """Replace each generated ``data-cid-*`` id with c0, c1, ... in order of first use."""
    names: dict[str, str] = {}

    def name(match: re.Match[str]) -> str:
        return f"data-cid-{names.setdefault(match.group(1), f'c{len(names)}')}"

    return re.sub(r"data-cid-(\w+)", name, html)


# Outer > Inner, where Inner's on_render hook passes its output to Frame.
_NESTED = '<main data-cid-c0=""> <section data-cid-c1="" data-cid-c2=""> <p>inner</p> </section> </main>'


class TestWrapReceivedOutputInAComponent:
    """A hook that passes the output it received to another component."""

    @staticmethod
    def _components(app: Citry) -> tuple[type[Component], type[Component]]:
        class Frame(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

            template = """
                <section>{{ body }}</section>
            """

        class Inner(Component):
            citry = app

            def on_render(self):
                result, _error = yield
                return Frame(body=result)

            template = """
                <p>inner</p>
            """

        return Frame, Inner

    @staticmethod
    def _outer(app: Citry) -> type[Component]:
        class Outer(Component):
            citry = app
            template = """
                <main><c-Inner /></main>
            """

        return Outer

    @staticmethod
    def _html(root: type[Component]) -> str:
        return " ".join(_named_cids(root().render().serialize(deps_strategy="ignore")).split())

    def test_the_passed_output_carries_no_marker_of_its_own(self, render_path):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False)
        _frame, inner = self._components(app)
        # Frame's section carries Frame's marker and Inner's, because the
        # section is the root of Inner's output now. The <p> is Inner's
        # content passed into Frame, as a nested template is, so it carries
        # no marker of its own.
        assert self._html(inner) == '<section data-cid-c0="" data-cid-c1=""> <p>inner</p> </section>'

    def test_nested_inside_another_component_it_writes_the_same_html(self, render_path):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False)
        _frame, inner = self._components(app)
        alone = self._html(inner)
        nested = self._html(self._outer(app))
        assert nested == _NESTED
        # The same markup as alone, with each id renamed past Outer's.
        shifted = re.sub(r"data-cid-c(\d+)", lambda m: f"data-cid-c{int(m.group(1)) + 1}", alone)
        assert nested == f'<main data-cid-c0=""> {shifted} </main>'

    def test_a_yielded_wrapper_works_nested_too(self, render_path):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False)

        class Frame(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

            template = """
                <section>{{ body }}</section>
            """

        class Inner(Component):
            citry = app

            def on_render(self):
                result, _error = yield
                yield Frame(body=result)

            template = """
                <p>inner</p>
            """

        assert self._html(self._outer(app)) == _NESTED

    @pytest.mark.parametrize(
        ("inner_cached", "outer_cached"),
        [(True, False), (False, True)],
        ids=["inner-cached", "outer-cached"],
    )
    def test_a_cache_hit_writes_the_same_html(self, inner_cached, outer_cached):
        app = Citry(autodiscover=False)

        class Frame(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

            template = """
                <section>{{ body }}</section>
            """

        class Inner(Component):
            citry = app

            class Cache:
                enabled = inner_cached

            def on_render(self):
                result, _error = yield
                return Frame(body=result)

            template = """
                <p>inner</p>
            """

        class Outer(Component):
            citry = app

            class Cache:
                enabled = outer_cached

            template = """
                <main><c-Inner /></main>
            """

        # The first render stores the output; the second one replays it.
        first = self._html(Outer)
        assert self._html(Outer) == first == _NESTED

    def test_an_on_component_rendered_hook_can_wrap_the_output_too(self, render_path):
        del render_path  # the fixture switches the render path
        frames: list[type[Component]] = []

        class WrapInner(Extension):
            name = "wrap_inner"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Inner":
                    return frames[0](body=ctx.render).render()
                return None

        app = Citry(autodiscover=False, extensions=[WrapInner])

        class Frame(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

            template = """
                <section>{{ body }}</section>
            """

        frames.append(Frame)

        class Inner(Component):
            citry = app
            template = """
                <p>inner</p>
            """

        assert self._html(self._outer(app)) == _NESTED

    @pytest.mark.parametrize("nested", [False, True], ids=["alone", "nested"])
    def test_the_same_output_placed_twice_is_still_an_error(self, render_path, nested):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False)

        class Pair(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"first": kwargs["first"], "second": kwargs["second"]}

            template = """
                <section>{{ first }}{{ second }}</section>
            """

        class Inner(Component):
            citry = app

            def on_render(self):
                result, _error = yield
                return Pair(first=result, second=result)

            template = """
                <p>inner</p>
            """

        # One output cannot sit in two places on the page.
        with pytest.raises(RuntimeError, match="encountered more than once"):
            self._html(self._outer(app) if nested else Inner)

    def test_two_wraps_in_a_row_nest_the_output_twice(self, render_path):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False)

        class Frame(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

            template = """
                <section>{{ body }}</section>
            """

        class Inner(Component):
            citry = app

            def on_render(self):
                result, _error = yield
                # The second wrap receives the first one's output.
                result, _error = yield Frame(body=result)
                return Frame(body=result)

            template = """
                <p>inner</p>
            """

        # The inner section is the first wrap's Frame. It is Inner's content
        # passed into the second Frame, so it carries only its own marker.
        assert self._html(self._outer(app)) == (
            '<main data-cid-c0=""> <section data-cid-c1="" data-cid-c2="">'
            ' <section data-cid-c3=""> <p>inner</p> </section>'
            " </section> </main>"
        )

    def test_two_components_side_by_side_each_keep_their_output(self, render_path):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False)
        self._components(app)

        class Outer(Component):
            citry = app
            template = """
                <main><c-Inner /><c-Inner /></main>
            """

        assert self._html(Outer) == (
            '<main data-cid-c0=""> <section data-cid-c1="" data-cid-c2=""> <p>inner</p> </section>'
            ' <section data-cid-c3="" data-cid-c4=""> <p>inner</p> </section> </main>'
        )

    def test_output_that_contains_itself_is_an_error(self):
        app = Citry(autodiscover=False)

        class First(Component):
            citry = app
            template = """
                <p>first</p>
            """

        class Second(Component):
            citry = app
            template = """
                <p>second</p>
            """

        first = First().render()
        second = Second().render()
        first.parts.append(second)
        second.parts.append(first)
        # Serialization stops at the loop instead of running forever.
        with pytest.raises(RuntimeError, match="encountered more than once"):
            first.serialize(deps_strategy="ignore")

    def test_a_development_page_does_not_report_the_kept_id_twice(self, render_path):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False, mode="development")

        class Frame(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

            template = """
                <section>{{ body }}</section>
            """

        class Inner(Component):
            citry = app

            def on_render(self):
                result, _error = yield
                return Frame(body=result)

            template = """
                <p id="intro">inner</p>
            """

        with warnings.catch_warnings():
            # The <p> is written once, so its id must not be reported as repeated.
            warnings.simplefilter("error", RuntimeWarning)
            html = self._html(self._outer(app))
        assert html.count('id="intro"') == 1

    def test_the_passed_output_inherits_css_variables_from_the_root(self, render_path):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False)

        class Frame(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

            template = """
                <section>{{ body }}</section>
            """

        class Inner(Component):
            citry = app

            def on_render(self):
                result, _error = yield
                return Frame(body=result)

            def css_data(self, kwargs, slots):
                return {"tone": "red"}

            template = """
                <p>inner</p>
            """

            css = """
                p { color: var(--tone); }
            """

        html = self._html(self._outer(app))
        found = re.search(r"data-ccss-[0-9a-f]{32}", html)
        assert found is not None
        marker = found.group()
        # The marker that css_data's variables target sits on Inner's root,
        # the section, and the <p> inside inherits the variables from it.
        assert html == (
            f'<main data-cid-c0=""> <section data-cid-c1="" data-cid-c2="" {marker}="">'
            " <p>inner</p> </section> </main>"
        )


def _vue_body(root: type[Component]) -> str:
    """Return the server HTML of a Vue page, without scripts, ids, or line-break whitespace between tags."""
    html = str(root()).split("<script", 1)[0]
    return _without_spaces_between_tags(re.sub(r"citry-vue-[0-9a-f]+", "citry-vue-ID", html))


def _without_spaces_between_tags(html: str) -> str:
    # Vue drops whitespace-only text between two tags when it holds a line
    # break, and turns any other run of whitespace into one space, so a
    # multiline template and a one-line one compile to the same output.
    return " ".join(re.sub(r">\s*\n\s*<", "><", html).split())


def _named_definitions(root: type[Component]) -> list[str]:
    """
    Return each compiled Vue template of a page, in the order its components occur.

    Generated slot and call names are numbered in order of first use, a
    component's tag loses its class id, and runs of whitespace become one
    space (none between two tags when it holds a line break), so two pages
    that compile the same way compare equal.
    """
    assembly = _assemble_prepared(root())
    names: dict[str, str] = {}

    def name(match: re.Match[str]) -> str:
        kind = match.group(1)
        if match.group(0) not in names:
            names[match.group(0)] = f"{kind}{sum(value.startswith(kind) for value in names.values())}"
        return names[match.group(0)]

    templates = [assembly.compile_inputs[item.definition_id].template for item in assembly.view.occurrences]
    named = []
    for template in dict.fromkeys(templates):
        numbered = re.sub(r"(citrySlot|citryCall)[0-9a-f]+", name, template)
        named.append(_without_spaces_between_tags(re.sub(r"x-([a-z]+)-[0-9a-f]+", r"x-\1", numbered)))
    return named


# What Inner compiles to on a Vue page when it passes its content to Frame
# as a nested template, `<c-frame c-body="<p>inner</p>" />`: Inner's
# definition fills a slot of Frame, and Frame prints that slot.
_NESTED_TEMPLATE_DEFINITIONS = [
    '<x-frame :citry-id="$citryPrepared.calls.citryCall0.id" :key="$citryPrepared.calls.citryCall0.key">'
    "<template v-slot:['citrySlot0']><p>inner</p></template></x-frame>",
    '<section><slot name="citrySlot0"></slot></section>',
]
_NESTED_TEMPLATE_BODY = '<div id="citry-vue-ID"><section><!--[--><p>inner</p><!--]--></section></div>'


def _vue_wrappers(app: Citry) -> None:
    """Register Frame, which prints its ``body`` input, and Shell, which prints its default slot."""

    class Frame(Component):
        citry = app
        name = "frame"

        def template_data(self, kwargs, slots):
            return {"body": kwargs["body"]}

        template = """
            <section>{{ body }}</section>
        """

    class Shell(Component):
        citry = app
        name = "shell"
        template = """
            <section><c-slot /></section>
        """


def _vue_pages(app: Citry, inner: type[Component]) -> dict[str, type[Component]]:
    """Return the pages that place ``inner``: alone, inside a template, and inside a slot fill."""

    class Outer(Component):
        citry = app
        template = """
            <main><c-inner /></main>
        """

    class Filled(Component):
        citry = app
        template = """
            <main><c-shell><c-inner /></c-shell></main>
        """

    return {"alone": inner, "nested": Outer, "in-a-fill": Filled}


def _named_prepared_data(root: type[Component]) -> str:
    """Return each occurrence's browser data, as JSON, with generated call, occurrence and slot names numbered."""
    assembly = _assemble_prepared(root())
    data = json.dumps([[item.type_key.split("_", 1)[0], item.prepared_data] for item in assembly.view.occurrences])
    names: dict[str, str] = {}

    def name(match: re.Match[str]) -> str:
        return names.setdefault(match.group(0), f"{match.group(1)}{len(names)}")

    return re.sub(r"(citryCall|citryOccurrence|citrySlotKey|citrySlot)[0-9a-f]+", name, data)


def _definitions_per_component(root: type[Component]) -> dict[str, int]:
    """Return how many separate Vue definitions each component class of a page compiles to."""
    assembly = _assemble_prepared(root())
    ids: dict[str, set[str]] = {}
    for item in assembly.view.occurrences:
        ids.setdefault(item.type_key.split("_", 1)[0], set()).add(item.definition_id)
    return {name: len(values) for name, values in ids.items()}


def _cache_hit_probe(hits: list[str]) -> type[Extension]:
    """Return an extension that records the class name of each component the cache replays."""

    class CacheHitProbe(Extension):
        name = "cache_hit_probe"

        def on_component_cache_hit(self, ctx):
            hits.append(type(ctx.component).__name__)

    return CacheHitProbe


class TestVueCompilesReceivedOutputInItsComponent:
    """
    On a Vue page, output an on_render hook passes to another component compiles in the hook's component.

    The output reaches the other component as content the hook's component
    wrote, the way a nested template does, not as a second copy of the
    hook's component inside itself.
    """

    @staticmethod
    def _nested_template_inner(app: Citry, *, cached: bool) -> type[Component]:
        class Inner(Component):
            citry = app
            name = "inner"

            class Cache:
                enabled = cached

            template = """
                <c-frame c-body="<p>inner</p>" />
            """
            js = """
                $component({});
            """

        return Inner

    # The tests below lock what the nested template does today, before the
    # on_render output reuses the same machinery.

    def test_a_nested_template_compiles_into_its_author(self):
        app = Citry(autodiscover=False)
        _vue_wrappers(app)
        inner = self._nested_template_inner(app, cached=False)
        assert _named_definitions(inner) == _NESTED_TEMPLATE_DEFINITIONS
        assert _vue_body(inner) == _NESTED_TEMPLATE_BODY

    def test_keyed_nested_template_authors_share_one_definition(self):
        app = Citry(autodiscover=False)
        _vue_wrappers(app)
        self._nested_template_inner(app, cached=False)

        class Rows(Component):
            citry = app
            template = """
                <main>
                    <c-for each="key in keys">
                        <c-inner #c-key="key" c-key="key" />
                    </c-for>
                </main>
            """

            def template_data(self, kwargs, slots):
                return {"keys": ["a", "b"]}

        # Each component has one definition for both rows, and the slot
        # name does not depend on the row.
        assert _definitions_per_component(Rows) == {"Rows": 1, "Inner": 1, "Frame": 1}
        assert _named_definitions(Rows) == [
            '<main><x-inner :citry-id="$citryPrepared.calls.citryCall0.id"'
            ' :key="$citryPrepared.calls.citryCall0.key"></x-inner>'
            '<x-inner :citry-id="$citryPrepared.calls.citryCall1.id"'
            ' :key="$citryPrepared.calls.citryCall1.key"></x-inner></main>',
            '<x-frame :citry-id="$citryPrepared.calls.citryCall2.id" :key="$citryPrepared.calls.citryCall2.key">'
            "<template v-slot:['citrySlot0']><p>inner</p></template></x-frame>",
            '<section><slot name="citrySlot0"></slot></section>',
        ]
        assert _vue_body(Rows) == (
            '<div id="citry-vue-ID"><main><section><!--[--><p>inner</p><!--]--></section>'
            "<section><!--[--><p>inner</p><!--]--></section></main></div>"
        )

    @pytest.mark.parametrize("page", ["alone", "nested", "in-a-fill"])
    def test_a_cached_nested_template_compiles_the_same_on_a_hit(self, page):
        hits: list[str] = []
        app = Citry(autodiscover=False, extensions=[_cache_hit_probe(hits)])
        _vue_wrappers(app)
        root = _vue_pages(app, self._nested_template_inner(app, cached=True))[page]
        stored = (_named_definitions(root), _vue_body(root))
        assert (_named_definitions(root), _vue_body(root)) == stored
        assert "Inner" in hits

    @pytest.mark.parametrize("page", ["alone", "nested"])
    def test_returning_the_received_output_writes_the_template_without_vue(self, render_path, page):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False)

        class Inner(Component):
            citry = app
            name = "inner"

            def on_render(self):
                result, _error = yield
                return result

            template = """
                <p>inner</p>
            """

        root = _vue_pages(app, Inner)[page]
        html = " ".join(_named_cids(root().render().serialize(deps_strategy="ignore")).split())
        assert (
            html
            == {
                "alone": '<p data-cid-c0="">inner</p>',
                "nested": '<main data-cid-c0=""> <p data-cid-c1="">inner</p> </main>',
            }[page]
        )

    def test_the_same_result_printed_twice_is_an_error(self):
        app = Citry(autodiscover=False)

        class Pair(Component):
            citry = app
            name = "pair"

            def template_data(self, kwargs, slots):
                return {"first": kwargs["first"], "second": kwargs["second"]}

            template = """
                <section>{{ first }}{{ second }}</section>
            """

        class Inner(Component):
            citry = app
            name = "inner"

            def on_render(self):
                result, _error = yield
                return Pair(first=result, second=result)

            template = """
                <p>inner</p>
            """
            js = """
                $component({});
            """

        with pytest.raises(RuntimeError, match="encountered more than once"):
            str(Inner())

    # The tests below are what the change makes work.

    @staticmethod
    def _hook_inner(app: Citry, *, shape: str, cached: bool = False) -> type[Component]:
        frame = app.get("frame")
        shell = app.get("shell")

        class Inner(Component):
            citry = app
            name = "inner"

            class Cache:
                enabled = cached

            def on_render(self):
                result, _error = yield
                if shape == "return":
                    return frame(body=result)
                if shape == "yield":
                    yield frame(body=result)
                    return None
                if shape == "slot":
                    return shell(slots={"default": result})
                return result

            template = """
                <p>inner</p>
            """
            js = """
                $component({});
            """

        return Inner

    @pytest.mark.parametrize("shape", ["return", "yield"])
    @pytest.mark.parametrize("page", ["alone", "nested", "in-a-fill"])
    def test_a_wrapped_result_compiles_like_a_nested_template(self, shape, page):
        reference_app = Citry(autodiscover=False)
        _vue_wrappers(reference_app)
        reference = _vue_pages(reference_app, self._nested_template_inner(reference_app, cached=False))[page]
        app = Citry(autodiscover=False)
        _vue_wrappers(app)
        root = _vue_pages(app, self._hook_inner(app, shape=shape))[page]
        assert _named_definitions(root) == _named_definitions(reference)
        assert _vue_body(root) == _vue_body(reference)
        assert _named_prepared_data(root) == _named_prepared_data(reference)

    @pytest.mark.parametrize("page", ["alone", "nested", "in-a-fill"])
    def test_a_cached_wrapped_result_compiles_the_same_on_a_hit(self, page):
        reference_app = Citry(autodiscover=False)
        _vue_wrappers(reference_app)
        reference = _vue_pages(reference_app, self._nested_template_inner(reference_app, cached=False))[page]
        hits: list[str] = []
        app = Citry(autodiscover=False, extensions=[_cache_hit_probe(hits)])
        _vue_wrappers(app)
        root = _vue_pages(app, self._hook_inner(app, shape="return", cached=True))[page]
        expected = (_named_definitions(reference), _vue_body(reference), _named_prepared_data(reference))
        assert (_named_definitions(root), _vue_body(root), _named_prepared_data(root)) == expected
        assert (_named_definitions(root), _vue_body(root), _named_prepared_data(root)) == expected
        assert "Inner" in hits

    def test_a_result_passed_as_a_slot_compiles_into_its_component(self):
        app = Citry(autodiscover=False)
        _vue_wrappers(app)
        inner = self._hook_inner(app, shape="slot")
        assert _named_definitions(inner) == [
            '<x-shell :citry-id="$citryPrepared.calls.citryCall0.id" :key="$citryPrepared.calls.citryCall0.key">'
            "<template v-slot:['citrySlot0']><p>inner</p></template></x-shell>",
            '<section><slot name="citrySlot0"></slot></section>',
        ]
        assert _vue_body(inner) == '<div id="citry-vue-ID"><section><!--[--><p>inner</p><!--]--></section></div>'

    @pytest.mark.parametrize("page", ["alone", "nested", "in-a-fill"])
    def test_returning_the_received_output_writes_the_template(self, page):
        plain_app = Citry(autodiscover=False)
        _vue_wrappers(plain_app)

        class Inner(Component):
            citry = plain_app
            name = "inner"
            template = """
                <p>inner</p>
            """
            js = """
                $component({});
            """

        plain = _vue_pages(plain_app, Inner)[page]
        app = Citry(autodiscover=False)
        _vue_wrappers(app)
        root = _vue_pages(app, self._hook_inner(app, shape="unwrapped"))[page]
        assert _named_definitions(root) == _named_definitions(plain)
        assert _vue_body(root) == _vue_body(plain)
        assert _named_prepared_data(root) == _named_prepared_data(plain)

    def test_its_own_nested_template_and_the_result_get_separate_slots(self):
        app = Citry(autodiscover=False)
        _vue_wrappers(app)
        frame = app.get("frame")

        class Inner(Component):
            citry = app
            name = "inner"

            def on_render(self):
                result, _error = yield
                return frame(body=result)

            template = """
                <c-frame c-body="<b>own</b>" />
            """
            js = """
                $component({});
            """

        class Rows(Component):
            citry = app
            template = """
                <main>
                    <c-for each="key in keys">
                        <c-inner #c-key="key" c-key="key" />
                    </c-for>
                </main>
            """

            def template_data(self, kwargs, slots):
                return {"keys": ["a", "b"]}

        # Inner's own nested template and the output its hook passes on are
        # two places Inner wrote content, so they fill two different slots.
        # The rows still share one definition of Inner; Frame has one for
        # each slot it prints.
        assert _definitions_per_component(Rows) == {"Rows": 1, "Inner": 1, "Frame": 2}
        assert _named_definitions(Rows) == [
            '<main><x-inner :citry-id="$citryPrepared.calls.citryCall0.id"'
            ' :key="$citryPrepared.calls.citryCall0.key"></x-inner>'
            '<x-inner :citry-id="$citryPrepared.calls.citryCall1.id"'
            ' :key="$citryPrepared.calls.citryCall1.key"></x-inner></main>',
            '<x-frame :citry-id="$citryPrepared.calls.citryCall2.id" :key="$citryPrepared.calls.citryCall2.key">'
            "<template v-slot:['citrySlot0']>"
            '<x-frame :citry-id="$citryPrepared.calls.citryCall3.id" :key="$citryPrepared.calls.citryCall3.key">'
            "<template v-slot:['citrySlot1']><b>own</b></template></x-frame>"
            "</template></x-frame>",
            '<section><slot name="citrySlot0"></slot></section>',
            '<section><slot name="citrySlot1"></slot></section>',
        ]
        assert _vue_body(Rows) == (
            '<div id="citry-vue-ID"><main>'
            "<section><!--[--><section><!--[--><b>own</b><!--]--></section><!--]--></section>"
            "<section><!--[--><section><!--[--><b>own</b><!--]--></section><!--]--></section>"
            "</main></div>"
        )

    @pytest.mark.parametrize("page", ["alone", "nested", "in-a-fill"])
    def test_an_on_component_rendered_wrap_compiles_like_a_nested_template(self, page):
        frames: list[type[Component]] = []

        class WrapInner(Extension):
            name = "wrap_inner"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Inner":
                    return frames[0](body=ctx.render).render()
                return None

        reference_app = Citry(autodiscover=False)
        _vue_wrappers(reference_app)
        reference = _vue_pages(reference_app, self._nested_template_inner(reference_app, cached=False))[page]
        app = Citry(autodiscover=False, extensions=[WrapInner])
        _vue_wrappers(app)
        frames.append(app.get("frame"))

        class Inner(Component):
            citry = app
            name = "inner"
            template = """
                <p>inner</p>
            """
            js = """
                $component({});
            """

        root = _vue_pages(app, Inner)[page]
        assert _named_definitions(root) == _named_definitions(reference)
        assert _vue_body(root) == _vue_body(reference)
        assert _named_prepared_data(root) == _named_prepared_data(reference)

    def test_two_wraps_in_a_row_compile_one_inside_the_other(self):
        app = Citry(autodiscover=False)
        _vue_wrappers(app)
        frame = app.get("frame")

        class Inner(Component):
            citry = app
            name = "inner"

            def on_render(self):
                result, _error = yield
                # The second wrap receives the first one's output.
                result, _error = yield frame(body=result)
                return frame(body=result)

            template = """
                <p>inner</p>
            """
            js = """
                $component({});
            """

        # Both Frames print the same slot, each filled by Inner, so they
        # share one definition.
        assert _definitions_per_component(Inner) == {"Inner": 1, "Frame": 1}
        assert _named_definitions(Inner) == [
            '<x-frame :citry-id="$citryPrepared.calls.citryCall0.id" :key="$citryPrepared.calls.citryCall0.key">'
            "<template v-slot:['citrySlot0']>"
            '<x-frame :citry-id="$citryPrepared.calls.citryCall1.id" :key="$citryPrepared.calls.citryCall1.key">'
            "<template v-slot:['citrySlot0']><p>inner</p></template></x-frame>"
            "</template></x-frame>",
            '<section><slot name="citrySlot0"></slot></section>',
        ]
        assert _vue_body(Inner) == (
            '<div id="citry-vue-ID"><section><!--[-->'
            "<section><!--[--><p>inner</p><!--]--></section>"
            "<!--]--></section></div>"
        )

    def test_a_parent_printing_a_rendered_component_still_calls_it(self):
        # Only the component's own hook passes its output on as content. A
        # parent that prints `Row().render()` gets an ordinary call of Row,
        # even when Row has an on_render hook.
        app = Citry(autodiscover=False)

        class Row(Component):
            citry = app
            name = "row"

            def on_render(self):
                _result, _error = yield

            template = """
                <p>row</p>
            """
            js = """
                $component({});
            """

        class Page(Component):
            citry = app

            def template_data(self, kwargs, slots):
                return {"row": Row().render()}

            template = """
                <main>{{ row }}</main>
            """

        assert _named_definitions(Page) == [
            '<main><x-row :citry-id="$citryPrepared.calls.citryCall0.id" :key="$citryPrepared.calls.citryCall0.key">'
            "</x-row></main>",
            "<p>row</p>",
        ]
        assert _vue_body(Page) == '<div id="citry-vue-ID"><main><p>row</p></main></div>'

    @staticmethod
    def _checking(app: Citry) -> type[Component]:
        # A Shell that calls its slot to look at it before printing it.
        class Checking(Component):
            citry = app
            name = "checking"

            def template_data(self, kwargs, slots):
                slots["default"]()
                return {}

            template = """
                <section><c-slot /></section>
            """

        return Checking

    # Only placing the output twice is an error. A Shell that calls its slot
    # to look at it, and a hook that renders a preview it drops, each
    # evaluate the output once more without placing it.

    def test_a_result_evaluated_and_dropped_first_still_renders_without_vue(self, render_path):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False)
        _vue_wrappers(app)
        frame = app.get("frame")
        checking = self._checking(app)

        class Inner(Component):
            citry = app
            name = "inner"

            def on_render(self):
                result, _error = yield
                frame(body=result).render()
                return checking(slots={"default": result})

            template = """
                <p>inner</p>
            """

        html = " ".join(_named_cids(Inner().render().serialize(deps_strategy="ignore")).split())
        assert html == '<section data-cid-c0="" data-cid-c1=""> <p>inner</p> </section>'

    def test_a_result_evaluated_and_dropped_first_still_renders_on_vue(self):
        app = Citry(autodiscover=False)
        _vue_wrappers(app)
        frame = app.get("frame")
        checking = self._checking(app)

        class Inner(Component):
            citry = app
            name = "inner"

            def on_render(self):
                result, _error = yield
                frame(body=result).render()
                return checking(slots={"default": result})

            template = """
                <p>inner</p>
            """
            js = """
                $component({});
            """

        assert _vue_body(Inner) == '<div id="citry-vue-ID"><section><!--[--><p>inner</p><!--]--></section></div>'

    def test_an_error_boundary_does_not_hide_the_result_printed_twice(self):
        # The second placement is found when the page is written, after the
        # render, so the boundary's fallback cannot replace the error.
        app = Citry(autodiscover=False)

        class Pair(Component):
            citry = app
            name = "pair"

            def template_data(self, kwargs, slots):
                return {"first": kwargs["first"], "second": kwargs["second"]}

            template = """
                <section>{{ first }}{{ second }}</section>
            """

        class Inner(Component):
            citry = app
            name = "inner"

            def on_render(self):
                result, _error = yield
                return Pair(first=result, second=result)

            template = """
                <p>inner</p>
            """
            js = """
                $component({});
            """

        class Guarded(Component):
            citry = app
            template = """
                <!doctype html>
                <html>
                    <head></head>
                    <body>
                        <c-error-fallback fallback="oops"><c-inner /></c-error-fallback>
                    </body>
                </html>
            """

        with pytest.raises(RuntimeError, match="encountered more than once"):
            str(Guarded())

    def test_an_error_boundary_does_not_hide_the_result_printed_twice_without_vue(self, render_path):
        del render_path  # the fixture switches the render path
        app = Citry(autodiscover=False)

        class Pair(Component):
            citry = app
            name = "pair"

            def template_data(self, kwargs, slots):
                return {"first": kwargs["first"], "second": kwargs["second"]}

            template = """
                <section>{{ first }}{{ second }}</section>
            """

        class Inner(Component):
            citry = app
            name = "inner"

            def on_render(self):
                result, _error = yield
                return Pair(first=result, second=result)

            template = """
                <p>inner</p>
            """

        class Guarded(Component):
            citry = app
            template = """
                <main><c-error-fallback fallback="oops"><c-inner /></c-error-fallback></main>
            """

        with pytest.raises(RuntimeError, match="encountered more than once"):
            Guarded().render().serialize(deps_strategy="ignore")

    def test_a_simple_receiver_prints_the_result_in_place(self):
        # A simple=True component renders in its caller's context, so the
        # output it prints is already the caller's own content.
        app = Citry(autodiscover=False)

        class Plain(Component):
            citry = app
            name = "plain"
            simple = True
            template = """
                <section>{{ body }}</section>
            """

        class Inner(Component):
            citry = app
            name = "inner"

            def on_render(self):
                result, _error = yield
                return Plain(body=result)

            template = """
                <p>inner</p>
            """
            js = """
                $component({});
            """

        assert _vue_body(Inner) == '<div id="citry-vue-ID"><section><p>inner</p></section></div>'

    def test_a_decorated_result_keeps_its_decoration(self):
        # The debug outline decorates Inner's output before the next
        # extension passes it to Frame; the outline stays around the content.
        frames: list[type[Component]] = []

        class WrapInner(Extension):
            name = "wrap_inner"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Inner":
                    return frames[0](body=ctx.render).render()
                return None

        app = Citry(
            autodiscover=False,
            extensions=[Debug, WrapInner],
            extensions_defaults={"debug": {"highlight_components": True}},
        )
        _vue_wrappers(app)
        frames.append(app.get("frame"))

        class Inner(Component):
            citry = app
            name = "inner"
            template = """
                <p>inner</p>
            """
            js = """
                $component({});
            """

        body = re.sub(r' style="[^"]*"| \(\w+\)', "", _vue_body(Inner))
        assert body == (
            '<div id="citry-vue-ID"><div class="citry-debug citry-debug-component">'
            '<span aria-hidden="true" class="citry-debug-label">Frame: </span><section><!--[-->'
            '<div class="citry-debug citry-debug-component">'
            '<span aria-hidden="true" class="citry-debug-label">Inner: </span><p>inner</p></div>'
            "<!--]--></section></div></div>"
        )

    def test_a_transparent_component_passes_its_result_on_like_a_nested_template(self):
        # A transparent component has no Vue definition, so its content
        # compiles in the template it is copied into, as its own nested
        # template would.
        reference_app = Citry(autodiscover=False)
        _vue_wrappers(reference_app)

        class Reference(Component):
            citry = reference_app
            name = "inner"
            transparent = True
            template = """
                <c-frame c-body="<p>inner</p>" />
            """

        app = Citry(autodiscover=False)
        _vue_wrappers(app)
        frame = app.get("frame")

        class Inner(Component):
            citry = app
            name = "inner"
            transparent = True

            def on_render(self):
                result, _error = yield
                return frame(body=result)

            template = """
                <p>inner</p>
            """

        reference = _vue_pages(reference_app, Reference)["nested"]
        root = _vue_pages(app, Inner)["nested"]
        assert _named_definitions(root) == _named_definitions(reference)
        assert _named_prepared_data(root) == _named_prepared_data(reference)

    @staticmethod
    def _tone_frame(app: Citry) -> type[Component]:
        class Frame(Component):
            citry = app
            name = "frame"

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

            def css_data(self, kwargs, slots):
                return {"tone": "blue"}

            template = """
                <section>{{ body }}</section>
            """
            css = """
                section { color: var(--tone); }
            """

        return Frame

    @staticmethod
    def _markers_per_element(html: str) -> list[tuple[str, list[str]]]:
        """List each element in the page body with the CSS-variables markers on it, in order."""
        # The page's scripts hold compiled templates, so read only the body.
        body = html[html.index("<main") : html.index("</main>")]
        return [
            (tag, sorted(re.findall(r"data-ccss-[0-9a-f]+", attrs)))
            for tag, attrs in re.findall(r"<(main|section|p)\b([^>]*)>", body)
        ]

    def test_the_markers_land_on_the_same_elements_with_and_without_vue(self):
        # Frame and Inner both set --tone. In both outputs the section, the
        # root of Inner's output, carries both markers, and the <p> Inner
        # passed into Frame carries none, so it inherits --tone from there.
        static_app = Citry(autodiscover=False)
        static_frame = self._tone_frame(static_app)

        class StaticInner(Component):
            citry = static_app
            name = "inner"

            def on_render(self):
                result, _error = yield
                return static_frame(body=result)

            def css_data(self, kwargs, slots):
                return {"tone": "red"}

            template = """
                <p>inner</p>
            """
            css = """
                p { color: var(--tone); }
            """

        vue_app = Citry(autodiscover=False)
        vue_frame = self._tone_frame(vue_app)

        class VueInner(Component):
            citry = vue_app
            name = "inner"

            def on_render(self):
                result, _error = yield
                return vue_frame(body=result)

            def css_data(self, kwargs, slots):
                return {"tone": "red"}

            template = """
                <p>inner</p>
            """
            js = """
                $component({});
            """
            css = """
                p { color: var(--tone); }
            """

        static_html = str(_vue_pages(static_app, StaticInner)["nested"]())
        vue_html = str(_vue_pages(vue_app, VueInner)["nested"]())
        assert "citry-vue-" not in static_html
        assert "citry-vue-" in vue_html
        static_markers = self._markers_per_element(static_html)
        assert self._markers_per_element(vue_html) == static_markers
        [(_main, main_markers), (_section, section_markers), (_p, p_markers)] = static_markers
        assert (main_markers, len(section_markers), p_markers) == ([], 2, [])
