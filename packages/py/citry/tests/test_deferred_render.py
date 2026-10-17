"""
Tests for deferred component rendering (docs/design/component_rendering_defer.md, Phase A).

``ComponentNode`` no longer recurses; it returns a ``DeferredComponent`` part,
and ``render_impl`` drives a heap-bound, depth-first queue that resolves every
deferred component. This frees render depth from Python's recursion limit
(``max_component_depth`` bounds it instead), keeps loop-variable kwargs
correct, fires ``on_component_rendered`` children-first the moment each
subtree is complete, and bubbles dependencies up at finalize time.
"""

# ruff: noqa: ANN

import pytest

from citry import Citry, CitryContext, CitryRender, Component, Markup
from citry.citry_render import DeferredComponent
from citry.extension import Extension


class TestInfiniteDepth:
    @pytest.mark.qualification
    def test_renders_far_past_recursion_limit(self):
        # A chain C0 -> C1 -> ... -> C600, each rendering the next. Eager
        # recursion blows the Python stack around ~60 levels; the queue is
        # heap-bound, so this must render.
        c = Citry()
        depth = 600

        for i in range(depth + 1):
            child_tag = f"<c-c{i + 1} />" if i < depth else "leaf"
            Component_i = type(
                f"C{i}",
                (Component,),
                {"citry": c, "template": f"<span>{child_tag}</span>"},
            )
            # Keep a reference alive so the class is not GC'd / unregistered.
            globals()[f"_C{i}"] = Component_i

        out = globals()["_C0"]().render().serialize()
        assert out.count("<span ") == depth + 1
        assert out.endswith("leaf" + "</span>" * (depth + 1))


class TestSelfRecursion:
    def test_guarded_self_recursion_renders_every_level_once(self):
        # A component that invokes its own tag, stopped by a kwarg-driven
        # c-if cutoff (the django-components recursive-component pattern).
        # Every level must emit its own markup, not just the leaf: each depth
        # marker appears exactly once, in depth order, parents wrapping
        # children. Depth is modest on purpose; extreme depth is
        # TestInfiniteDepth's job.
        c = Citry()
        limit = 6

        class Recursive(Component):
            citry = c
            template = (
                "<div><span>d{{ depth }};</span>"
                '<c-if cond="depth <= limit"><c-recursive c-depth="depth" /></c-if>'
                "</div>"
            )

            def template_data(self, kwargs, slots):
                # The root call has no kwargs; each self-call passes its
                # current depth, so the child renders at depth + 1.
                return {"depth": kwargs.get("depth", 0) + 1, "limit": limit}

        assert Recursive().render().serialize() == (
            '<div data-cid-c1=""><span>d1;</span>'
            '<div data-cid-c2=""><span>d2;</span>'
            '<div data-cid-c3=""><span>d3;</span>'
            '<div data-cid-c4=""><span>d4;</span>'
            '<div data-cid-c5=""><span>d5;</span>'
            '<div data-cid-c6=""><span>d6;</span>'
            '<div data-cid-c7=""><span>d7;</span>'
            "</div></div></div></div></div></div></div>"
        )


def _tree_class(app, *, simple=False):
    """A component that renders itself once per child of its ``node`` input."""
    attrs = {
        "citry": app,
        "simple": simple,
        "template": """
            <div>
              {{ label }}
              <c-for each="child in children">
                <c-tree c-node="child" />
              </c-for>
            </div>
        """,
    }

    def data(kwargs, slots):
        node = kwargs["node"]
        return {"label": node["label"], "children": node.get("children", [])}

    def method(self, kwargs, slots):
        return data(kwargs, slots)

    # A simple component's template_data takes no instance.
    attrs["template_data"] = staticmethod(data) if simple else method
    return type("Tree", (Component,), attrs)


def _chain(depth):
    """A tree with one node per level, ``depth`` levels deep."""
    node = {"label": "leaf"}
    for level in range(depth - 1):
        node = {"label": f"n{level}", "children": [node]}
    return node


def _self_containing_tree():
    """A tree listed among its own children, so it never reaches a leaf."""
    tree = {"label": "root", "children": []}
    tree["children"].append(tree)
    return tree


class TestNestingLimit:
    def test_self_containing_data_fails_with_the_repeating_component(self):
        # Without the limit, the work list grows forever (memory climbs until
        # the process dies). The default limit must stop it with an error
        # that names the component and shortens the chain of ancestors.
        Tree = _tree_class(Citry())

        with pytest.raises(RecursionError) as caught:
            Tree(node=_self_containing_tree()).render()

        assert str(caught.value).startswith(
            "Component Tree is nested more than 2000 components deep (Tree > Tree > ... > Tree > Tree > Tree). "
        )
        assert "max_component_depth" in str(caught.value)

    @pytest.mark.parametrize("simple", [False, True, "vue"])
    def test_limit_allows_exactly_max_component_depth_levels(self, simple):
        # Ordinary, simple=True, and simple="vue" children reach the work
        # list differently; each must count one level per component.
        Tree = _tree_class(Citry(max_component_depth=5), simple=simple)

        html = Tree(node=_chain(5)).render().serialize()
        assert "leaf" in html
        with pytest.raises(RecursionError, match="nested more than 5 components deep"):
            Tree(node=_chain(6)).render()

    def test_deep_finite_tree_renders_under_the_default_limit(self):
        Tree = _tree_class(Citry())

        html = Tree(node=_chain(500)).render().serialize()
        assert html.count("<div") == 500
        assert "leaf" in html

    def test_recursion_through_slot_content_is_limited(self):
        # The recursive call sits in fill content that another component
        # renders, so the child reaches the work list through a slot.
        c = Citry(max_component_depth=20)

        class Wrap(Component):
            citry = c
            template = """
                <section><c-slot /></section>
            """

        class SlotTree(Component):
            citry = c
            template = """
                <div>
                  <c-for each="child in children">
                    <c-wrap><c-slot-tree c-node="child" /></c-wrap>
                  </c-for>
                </div>
            """

            def template_data(self, kwargs, slots):
                return {"children": kwargs["node"].get("children", [])}

        with pytest.raises(RecursionError, match="SlotTree is nested more than 20 components deep"):
            SlotTree(node=_self_containing_tree()).render()

    def test_error_boundary_cannot_catch_the_nesting_error(self):
        # A node listed twice among its own children, under an error
        # boundary at every level: if a boundary swallowed the error, the
        # next sibling would recurse again and the work would double with
        # each level. The error must end the whole render instead.
        c = Citry(max_component_depth=20)
        rendered = []

        class Tree(Component):
            citry = c
            template = """
                <div>
                  <c-error-fallback fallback="!">
                    <c-for each="child in children">
                      <c-tree c-node="child" />
                    </c-for>
                  </c-error-fallback>
                </div>
            """

            def template_data(self, kwargs, slots):
                rendered.append(1)
                return {"children": kwargs["node"]["children"]}

        tree = {"children": []}
        tree["children"].extend([tree, tree])

        with pytest.raises(RecursionError, match="nested more than 20 components deep"):
            Tree(node=tree).render()
        # One straight path down to the limit, no retries through siblings:
        # each level is a Tree plus its error boundary, so 20 levels hold
        # 10 Trees.
        assert len(rendered) == 10

    def test_on_render_that_returns_itself_is_limited(self):
        # Each replacement is a new component inside the previous one, so a
        # replacement that always returns the same component nests forever.
        c = Citry(max_component_depth=20)

        class Again(Component):
            citry = c
            template = """
                <p>never shown</p>
            """

            def on_render(self):
                return Again()

        with pytest.raises(RecursionError, match="Again is nested more than 20 components deep"):
            Again().render()


class TestLoopVarKwargs:
    def test_loop_variable_resolved_eagerly_per_iteration(self):
        # Each <c-card> kwarg references the loop variable `i`. Kwargs must be
        # resolved while the per-iteration context is live, not at drive time.
        c = Citry()

        class Card(Component):
            citry = c
            template = "<b>{{ n }}</b>"

            def template_data(self, kwargs, slots):
                return {"n": kwargs["n"]}

        class Page(Component):
            citry = c
            template = '<ul><c-for each="i in items"><c-card c-n="i" /></c-for></ul>'

            def template_data(self, kwargs, slots):
                return {"items": [1, 2, 3]}

        assert Page().render().serialize() == (
            '<ul data-cid-c1=""><b data-cid-c2="">1</b><b data-cid-c3="">2</b><b data-cid-c4="">3</b></ul>'
        )


class TestFinalizeOrder:
    def _order_recorder(self):
        order: list[str] = []

        class Recorder(Extension):
            name = "recorder"

            def on_component_rendered(self, ctx):
                order.append(type(ctx.component).__name__)

        return order, Recorder

    def test_children_finalize_before_parents(self):
        order, Recorder = self._order_recorder()
        c = Citry(extensions=[Recorder])

        class Leaf(Component):
            citry = c
            template = "<i>leaf</i>"

        class Mid(Component):
            citry = c
            template = "<div><c-leaf /></div>"

        class Root(Component):
            citry = c
            template = "<main><c-mid /></main>"

        Root().render().serialize()
        assert order == ["Leaf", "Mid", "Root"]

    def test_siblings_finalize_in_source_order(self):
        order, Recorder = self._order_recorder()
        c = Citry(extensions=[Recorder])

        class A(Component):
            citry = c
            template = "<i>a</i>"

        class B(Component):
            citry = c
            template = "<i>b</i>"

        class Root(Component):
            citry = c
            template = "<main><c-a /><c-b /></main>"

        Root().render().serialize()
        assert order == ["A", "B", "Root"]


class TestDepsBubble:
    def test_descendant_deps_reach_root_extra(self):
        # Each component stashes its own marker into its render context's
        # extra. Bubbling is extension-owned: the finalize-time merge fires
        # on_render_context_merge, and the extension carries its own slice (here a set
        # of names) from the child context into the parent, all the way to
        # the root's extra.
        class Stash(Extension):
            name = "stash"

            def on_component_data(self, ctx):
                ctx.context.extra.setdefault("stash", set()).add(type(ctx.component).__name__)

            def on_render_context_merge(self, ctx):
                child = ctx.child_context.extra.get("stash")
                if child:
                    ctx.parent_context.extra.setdefault("stash", set()).update(child)

        c = Citry(extensions=[Stash])

        class Leaf(Component):
            citry = c
            template = "<i>x</i>"

        class Mid(Component):
            citry = c
            template = "<div><c-leaf /></div>"

        class Root(Component):
            citry = c
            template = "<main><c-mid /></main>"

        rendered = Root().render()
        assert rendered.context.extra["stash"] == {"Leaf", "Mid", "Root"}


class TestSerializeGuard:
    def test_unresolved_deferred_raises_on_serialize(self):
        ctx = CitryContext()
        # A DeferredComponent left in parts means the drive loop never ran.
        bogus = DeferredComponent.__new__(DeferredComponent)  # no element needed
        rendered = CitryRender(parts=["<p>", bogus, "</p>"], context=ctx)
        with pytest.raises(RuntimeError, match="unresolved DeferredComponent"):
            rendered.serialize()


class TestNestedRenderedHook:
    def test_string_replace_through_nested_tree(self):
        # on_component_rendered returning a string replaces a *nested* child's
        # output (not just the root), spliced back into the parent.
        class WrapLeaf(Extension):
            name = "wrap_leaf"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Leaf":
                    return Markup("<leaf-wrapped/>")
                return None

        c = Citry(extensions=[WrapLeaf])

        class Leaf(Component):
            citry = c
            template = "<i>leaf</i>"

        class Root(Component):
            citry = c
            template = "<main><c-leaf /></main>"

        assert Root().render().serialize() == '<main data-cid-c1=""><leaf-wrapped data-cid-c2=""/></main>'

    def test_raise_through_nested_tree_propagates(self):
        class BoomLeaf(Extension):
            name = "boom_leaf"

            def on_component_rendered(self, ctx):
                if type(ctx.component).__name__ == "Leaf":
                    raise ValueError("boom")

        c = Citry(extensions=[BoomLeaf])

        class Leaf(Component):
            citry = c
            template = "<i>leaf</i>"

        class Root(Component):
            citry = c
            template = "<main><c-leaf /></main>"

        with pytest.raises(ValueError, match="boom"):
            Root().render().serialize()
