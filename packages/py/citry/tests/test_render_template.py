from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import pytest

from citry import Citry, Component, Extension, ForeignSpan, ForeignSpanSet
from citry.nodes import ForeignNode


def test_render_template_is_a_transparent_root_with_variables_and_slots() -> None:
    app = Citry()

    rendered = app.render_template(
        "<p>{{ self }} {{ slots }}</p><c-slot>fallback</c-slot>",
        {"self": "S", "slots": "V"},
        slots={"default": "filled"},
    )

    assert str(rendered) == "<p>S V</p>filled"
    assert all("templateroot" not in name for name in app.components)


def test_render_template_renders_registered_components_normally() -> None:
    app = Citry()

    class Badge(Component):
        citry = app
        template = "<b>{{ label }}</b>"

        class Kwargs:
            label: str

    rendered = app.render_template('<section><c-badge label="new"/></section>')

    assert str(rendered) == '<section><b data-cid-c2="">new</b></section>'


def test_render_template_caches_load_span_and_compile_work_once_across_threads() -> None:
    calls = {"loaded": 0, "spans": 0, "compiled": 0}

    class Host(Extension):
        name = "host"

        def on_template_loaded(self, ctx):
            if ctx.template_kind == "standalone":
                calls["loaded"] += 1

        def on_template_foreign_spans(self, ctx):
            if ctx.template_kind != "standalone":
                return None
            calls["spans"] += 1
            start = ctx.content.encode().find(b"{% value %}")
            return ForeignSpanSet((ForeignSpan(start, start + len(b"{% value %}")),))

        def on_template_foreign_compiled(self, ctx):
            calls["compiled"] += 1
            ctx.nodes[:] = ["HOST" if isinstance(item, ForeignNode) else item for item in ctx.nodes]
            ctx.mark_resolved(*ctx.claims)

    app = Citry(extensions=[Host])
    app.initialize()

    def render() -> str:
        return str(app.render_template("A{% value %}B", origin="threaded"))

    with ThreadPoolExecutor(max_workers=4) as executor:
        assert list(executor.map(lambda _index: render(), range(8))) == ["AHOSTB"] * 8

    assert calls == {"loaded": 1, "spans": 1, "compiled": 1}


def test_render_template_clear_drops_the_standalone_cache() -> None:
    app = Citry()
    first = app.render_template("hello")
    first_id = next(iter(app._standalone_template_cache.values())).template_id
    assert str(first) == "hello"

    app.clear()
    second = app.render_template("hello")
    second_id = next(iter(app._standalone_template_cache.values())).template_id

    assert str(second) == "hello"
    assert first_id != second_id


def test_render_template_cache_tracks_component_registry_changes() -> None:
    app = Citry()

    class First(Component):
        citry = app
        name = "swappable"
        template = "<b>first</b>"

    assert ">first<" in str(app.render_template("<c-swappable/>"))

    app.unregister(First)

    class Second(Component):
        citry = app
        name = "swappable"
        template = "<i>second</i>"

    assert ">second<" in str(app.render_template("<c-swappable/>"))


def test_rejected_registration_drops_templates_compiled_against_transient_registry() -> None:
    class RejectAfterRender(Extension):
        name = "reject_after_standalone_render"

        def on_component_registered(self, ctx):
            if ctx.component_class.__name__ != "Rejected":
                return
            ctx.citry.render_template("<c-rejected/>")
            assert ctx.citry._standalone_template_cache
            raise RuntimeError("reject component")

    app = Citry(extensions=[RejectAfterRender], autodiscover=False)

    with pytest.raises(RuntimeError, match="reject component"):

        class Rejected(Component):
            citry = app

    assert not app._standalone_template_cache


def test_render_template_runtime_error_uses_the_standalone_origin() -> None:
    app = Citry()

    with pytest.raises(KeyError) as exc_info:
        app.render_template("{{ missing }}", origin="standalone-origin")

    assert "standalone-origin" in str(exc_info.value)


def test_foreign_compile_context_is_private_and_part_of_cache_identity() -> None:
    seen: list[str] = []

    @dataclass(frozen=True)
    class CompileContext:
        value: str
        provider: str = "host"

        @property
        def cache_fingerprint(self) -> str:
            return self.value

    class Host(Extension):
        name = "host"

        def on_template_foreign_spans(self, ctx):
            assert isinstance(ctx.compile_context, CompileContext)
            seen.append(ctx.compile_context.value)
            return ForeignSpanSet((ForeignSpan(0, len(ctx.content.encode())),), ctx.compile_context.value)

        def on_template_foreign_compiled(self, ctx):
            ctx.nodes[:] = [str(ctx.provider_metadata)]
            ctx.mark_resolved(*ctx.claims)

    app = Citry(extensions=[Host])
    first = CompileContext("one")
    second = CompileContext("two")

    assert str(app.render_template("HOST", foreign_compile_contexts=[first])) == "one"
    assert str(app.render_template("HOST", foreign_compile_contexts=[first])) == "one"
    assert str(app.render_template("HOST", foreign_compile_contexts=[second])) == "two"
    assert seen == ["one", "two"]
