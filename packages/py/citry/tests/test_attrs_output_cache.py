"""Qualified reuse of already-validated node attribute output."""

import gc
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from weakref import ref

import pytest

from citry import Citry, Component, Const, Markup, attrs, nodes
from citry.util import html


@pytest.fixture
def output_cache(monkeypatch):
    cache = {}
    monkeypatch.setattr(nodes, "_attrs_output_cache", cache)
    return cache


def make_node():
    return nodes.ElementAttrsNode("<div>", (0, 5), (), ())


def render(node, values, *, validate=False):
    return node._format(values, None, validate_keys=validate)


def test_cache_preserves_value_changes_types_order_and_escaping(output_cache):
    node = make_node()
    inputs = {"title": '<&"', "data-n": True}
    assert render(node, inputs) == ' title="&lt;&amp;&#34;" data-n'
    if html._CACHEABLE_ESCAPE_BACKEND:
        assert output_cache
    inputs["data-n"] = 1
    assert render(node, inputs) == ' title="&lt;&amp;&#34;" data-n="1"'
    inputs["data-n"] = False
    assert render(node, inputs) == ' title="&lt;&amp;&#34;"'
    inputs["title"] = "new"
    assert render(node, inputs) == ' title="new"'
    assert render(node, {"data-n": 1, "title": "new"}) == ' data-n="1" title="new"'
    assert render(node, {}) == ""
    assert render(node, {}) == ""


@pytest.mark.parametrize("warm", [False, True])
@pytest.mark.parametrize(
    ("owner", "name"),
    [
        (attrs, "_underlying"),
        (attrs, "_html_attr_identity"),
        (attrs, "escape_to_str"),
        (html, "_escape_to_str_impl"),
        (nodes, "_format_resolved_attrs_to_str"),
    ],
)
def test_helper_replacements_execute_before_first_use_and_after_hits(output_cache, monkeypatch, warm, owner, name):
    original = getattr(owner, name)
    if original is None:
        pytest.skip("This MarkupSafe version has no private escaper")
    node = make_node()
    if warm:
        render(node, {"title": "value"})
    calls = []

    def replacement(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(owner, name, replacement)
    assert render(node, {"title": "value"}) == ' title="value"'
    first = len(calls)
    assert first > 0
    assert render(node, {"title": "value"}) == ' title="value"'
    assert len(calls) > first


def test_backend_replaced_before_citry_import_never_becomes_trusted():
    source = """
import markupsafe._speedups as speedups
original = speedups._escape_inner
calls = []
def replacement(value):
    calls.append(value)
    return original(value)
speedups._escape_inner = replacement
from citry import nodes
from citry.util import html
assert not html._CACHEABLE_ESCAPE_BACKEND
node = nodes.ElementAttrsNode('<div>', (0, 5), (), ())
for _ in range(2):
    assert node._format({'title': 'value'}, None, validate_keys=False) == ' title="value"'
assert len(calls) == 4
assert not nodes._attrs_output_cache
"""
    if not html._CACHEABLE_ESCAPE_BACKEND:
        pytest.skip("This interpreter does not use the MarkupSafe C backend")
    package_root = str(Path(nodes.__file__).resolve().parents[2])
    result = subprocess.run(
        [sys.executable, "-c", source],
        env={**os.environ, "PYTHONPATH": os.pathsep.join((package_root, os.environ.get("PYTHONPATH", "")))},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_validation_and_custom_tag_getters_remain_live(output_cache):
    class CustomNode(nodes.ElementAttrsNode):
        @property
        def tag_name(self):
            self.reads += 1
            return "custom"

    node = CustomNode("<custom>", (0, 8), (), ())
    node.reads = 0
    for _ in range(2):
        assert render(node, {"title": "same"}, validate=True) == ' title="same"'
    assert node.reads == 2
    assert output_cache == {}
    ordinary = make_node()
    render(ordinary, {"bad name": "value"})
    with pytest.raises(ValueError, match="attributes resolved for <div>"):
        render(ordinary, {"bad name": "value"}, validate=True)


def test_protocols_proxies_and_mutable_class_values_remain_live(output_cache):
    class Content:
        def __init__(self):
            self.calls = 0

        def __html__(self):
            self.calls += 1
            return str(self.calls)

    node = make_node()
    value = Content()
    assert render(node, {"title": value}) == ' title="1"'
    assert render(node, {"title": value}) == ' title="2"'
    flags = {"active": True}
    assert render(node, {"class": flags}) == ' class="active"'
    flags["active"] = False
    assert render(node, {"class": flags}) == ""
    assert render(node, {"title": Markup("<b>")}) == ' title="<b>"'
    assert render(node, {"title": Const("x")}) == ' title="x"'
    assert output_cache == {}


def test_cache_does_not_retain_nodes_or_contexts(output_cache):
    class Context:
        pass

    node, context = make_node(), Context()
    node_ref, context_ref = ref(node), ref(context)
    assert node._format({"title": "value"}, context, validate_keys=False) == ' title="value"'
    del node, context
    gc.collect()
    assert node_ref() is None
    assert context_ref() is None


def test_independent_engines_and_clear_keep_input_callbacks_live(output_cache):
    first, second = Citry(), Citry()
    calls = []
    data = {"title": "same"}

    def make_component(engine):
        class Example(Component):
            citry = engine

            def template_data(self, kwargs, slots):
                calls.append(self.citry)
                return dict(data)

            template = """
                <div c-title="title"></div>
            """

        return Example

    first_component, second_component = make_component(first), make_component(second)

    def output(component):
        return component().render().serialize(deps_strategy="simple")

    assert 'title="same"' in output(first_component)
    assert 'title="same"' in output(second_component)
    if html._CACHEABLE_ESCAPE_BACKEND:
        assert output_cache
    first.clear()
    data["title"] = "changed<&"
    assert 'title="changed&lt;&amp;"' in output(first_component)
    assert 'title="changed&lt;&amp;"' in output(second_component)
    assert calls == [first, second, first, second]


def test_oversized_inputs_do_not_enter_cache(output_cache):
    node = make_node()
    for values in ({"title": "x" * 2049}, {f"k{i}": i for i in range(17)}, {"data-n": 1 << 256}):
        assert render(node, values)
    assert output_cache == {}


def test_miss_formats_the_values_in_its_cache_key(output_cache, monkeypatch):
    if not html._CACHEABLE_ESCAPE_BACKEND:
        pytest.skip("Caching is inactive on this backend")
    values = {"title": "before"}

    class MutatingCache(dict):
        def get(self, key, default=None):
            values["title"] = "after"
            return super().get(key, default)

    monkeypatch.setattr(nodes, "_attrs_output_cache", MutatingCache())
    node = make_node()
    assert render(node, values) == ' title="before"'
    assert render(node, values) == ' title="after"'
    assert render(node, {"title": "before"}) == ' title="before"'


def test_concurrent_misses_preserve_fifo_bound(output_cache, monkeypatch):
    if not html._CACHEABLE_ESCAPE_BACKEND:
        pytest.skip("Caching is inactive on this backend")
    barrier = Barrier(8)

    class ConcurrentCache(dict):
        def get(self, key, default=None):
            result = super().get(key, default)
            if result is None and key[0][2].startswith("thread-"):
                barrier.wait(timeout=10)
            return result

        def __setitem__(self, key, value):
            super().__setitem__(key, value)
            assert len(self) <= 256

    cache = ConcurrentCache()
    monkeypatch.setattr(nodes, "_attrs_output_cache", cache)
    node = make_node()
    for i in range(255):
        render(node, {"title": str(i)})

    def invoke(i):
        return render(node, {"title": f"thread-{i}"})

    with ThreadPoolExecutor(max_workers=8) as pool:
        actual = list(pool.map(invoke, range(64)))
    assert actual == [f' title="thread-{i}"' for i in range(64)]
    assert len(cache) == 256
