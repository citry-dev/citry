"""Preview declarations, structured composition, and command route contracts."""

import inspect
import json
import re
from pathlib import Path

import pytest

from citry import Citry, Component
from citry.ext.preview.extension import PreviewExtension, Selection
from citry.ext.preview.rendering import PreviewRenderer
from citry.ext.preview.routes import preview_routes
from citry.ext.preview.types import Layout, PreviewError, Viewport, variant
from citry.util.routing import RouteRequest, flatten_routes, match_route


def _app():
    app = Citry(extensions=[PreviewExtension])
    app.set_mounted_prefix("/citry")
    return app, app.extensions.get_extension("preview")


def _html(renderer, component, slug="default", **kwargs):
    return renderer.render_page(component.class_id, slug, **kwargs).serialize(deps_strategy="document")


def _route(renderer, path, query=None, method="GET"):
    match = match_route(preview_routes(renderer), path)
    assert match is not None
    return match.route.handler(RouteRequest(method=method, path=path, query=query or {}), **match.params)


def test_defaults_opt_in_inheritance_and_opt_out():
    app, ext = _app()

    class Plain(Component):
        citry = app
        template = """
            <p>plain</p>
        """

    class Parent(Component):
        citry = app
        template = """
            <p>parent</p>
        """

        class Preview:
            enabled = True
            group = "Elements"

    class Child(Parent):
        pass

    class Disabled(Parent):
        class Preview:
            enabled = False

    rows = ext.previews()
    assert {row.component for row in rows} == {Parent, Child}
    assert all(row.config.group == "Elements" for row in rows)
    assert all(row.variants[0].slug == "default" for row in rows)
    with pytest.raises(PreviewError, match="no enabled previews"):
        ext.previews(Selection(names=("Plain",)))
    assert not any(path.startswith("ext/preview") for path, _ in flatten_routes(app.urls))


def test_variant_inputs_are_fresh_and_variant_filter_is_strict():
    app, ext = _app()

    class Button(Component):
        citry = app
        template = """
            <button>{{ label }}</button>
        """

        class Preview:
            def variants(self):
                return [variant(slug="one", label="One", params={"label": []}), variant(slug="two", label="Two")]

    first = ext.previews()[0].variants[0]
    first.params["label"].append("changed")
    assert ext.previews()[0].variants[0].params["label"] == []
    assert [v.slug for v in ext.previews(Selection(variants=("two",)))[0].variants] == ["two"]
    with pytest.raises(PreviewError, match="Missing requested variants"):
        ext.previews(Selection(variants=("missing",)))
    with pytest.raises(PreviewError, match="Unknown preview component"):
        ext.previews(Selection(names=("Missing",)))


def test_duplicate_slugs_and_unknown_fields_are_errors():
    app, ext = _app()
    with pytest.raises(ValueError, match="Unknown Preview field"):

        class Typo(Component):
            citry = app

            class Preview:
                viewportt = Viewport()

    class Duplicate(Component):
        citry = app
        template = """
            <p />
        """

        class Preview:
            def variants(self):
                return [variant(slug="same", label="First"), variant(slug="same", label="Second")]

    with pytest.raises(PreviewError, match="duplicate slugs"):
        ext.previews()


@pytest.mark.parametrize(
    "kwargs", [{"slug": "../x"}, {"slug": "Upper"}, {"slug": "a--b"}, {"label": " "}, {"params": {1: 2}}]
)
def test_invalid_variant_declarations(kwargs):
    with pytest.raises(PreviewError):
        variant(**({"slug": "default", "label": "Default"} | kwargs))


def test_directory_filters_and_two_engines():
    app, ext = _app()
    other, other_ext = _app()

    class Here(Component):
        citry = app
        template = """
            <p />
        """

        class Preview:
            enabled = True

    class Elsewhere(Component):
        citry = other
        template = """
            <p />
        """

        class Preview:
            enabled = True

    cwd = Path(__file__).resolve().parent
    assert ext.previews(Selection(dirs=("**/test_preview.py",), cwd=cwd))[0].component is Here
    assert other_ext.previews()[0].component is Elsewhere
    with pytest.raises(PreviewError, match="excluded"):
        ext.previews(Selection(names=("Here",), dirs=("elsewhere",), cwd=cwd))
    with pytest.raises(PreviewError, match="relative paths"):
        Selection(dirs=("../outside",))


def test_direct_render_params_assets_fresh_ids_and_catalog_redaction():
    app, ext = _app()

    class Button(Component):
        citry = app
        template = """
            <button>{{ label }}</button>
        """
        css = """
            button { color: purple; }
        """

        class Preview:
            def variants(self):
                return [variant(slug="default", label="Display label", params={"label": "<Save>"})]

        def template_data(self, kwargs, slots):
            return kwargs

    renderer = PreviewRenderer(ext)
    first, second = _html(renderer, Button), _html(renderer, Button)
    assert "&lt;Save&gt;" in first
    assert "<!doctype html>" in first.lower()
    assert ".css" in first
    assert set(re.findall(r"data-cid-([\w-]+)", first)).isdisjoint(re.findall(r"data-cid-([\w-]+)", second))
    catalog = renderer.catalog()
    assert catalog["service"] == "citry-preview"
    text = json.dumps(catalog)
    assert "<Save>" not in text
    assert "params" not in text
    assert "python_file" not in text


def test_template_and_repeated_layout_slots_keep_provides_and_ids():
    app, ext = _app()
    observed = []

    class Consumer(Component):
        citry = app
        template = """
            <strong>{{ value }}:{{ outer }}:{{ text }}</strong>
        """
        css = """
            strong { color: purple; }
        """

        def template_data(self, kwargs, slots):
            observed.append((self.inject("theme").value, self.inject("outer")))
            return {"value": self.inject("theme").value, "outer": self.inject("outer"), "text": kwargs["text"]}

    class Example(Component):
        citry = app
        template = """
            <p>ordinary</p>
        """

        class Preview:
            template = """
                <c-consumer c-text="params['text']" />
            """
            variant_layout = Layout(
                template='<c-provide key="theme" value="violet"><c-slot name="content" /></c-provide>'
            )
            page_layout = Layout(
                template='<html><head></head><body><c-slot name="content" /><c-slot name="content" /></body></html>'
            )

            def variants(self):
                return [variant(slug="default", label="Example", params={"text": "hello"})]

    html = _html(PreviewRenderer(ext), Example, provides={"outer": "root"})
    assert html.count("violet:root:hello") == 2
    assert observed == [("violet", "root"), ("violet", "root")]
    tags = re.findall(r"<strong[^>]*>", html)
    assert len(tags) == 2
    assert tags[0] != tags[1]
    assert html.count('.css"') == 1


def test_component_layout_receives_metadata_and_content():
    app, ext = _app()

    class Frame(Component):
        citry = app
        template = """
            <aside><h2>{{ label }}</h2><c-slot name="content" /></aside>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["preview"].variant.label}

    class Example(Component):
        citry = app
        template = """
            <p>example</p>
        """

        class Preview:
            enabled = True
            variant_layout = Layout(component=Frame)

    html = _html(PreviewRenderer(ext), Example)
    assert "<aside" in html
    assert "example</p>" in html
    assert "example</h2>" in html


def test_preview_files_are_read_again_and_missing_files_fail(tmp_path):
    app, ext = _app()
    source = tmp_path / "preview.html"
    source.write_text("<p>first</p>")

    class Example(Component):
        citry = app
        template = """
            <p>ordinary</p>
        """

        class Preview:
            template_file = source

    renderer = PreviewRenderer(ext)
    assert "first</p>" in _html(renderer, Example)
    source.write_text("<p>second</p>")
    assert "second</p>" in _html(renderer, Example)
    source.unlink()
    with pytest.raises(PreviewError, match="Cannot read"):
        _html(renderer, Example)


def test_gallery_escapes_labels_preserves_viewport_and_filters():
    app, ext = _app()

    class First(Component):
        citry = app
        template = """
            <p />
        """

        class Preview:
            def variants(self):
                return [
                    variant(
                        slug="default",
                        label='<img src=x onerror="bad">',
                        description="<script>bad</script>",
                        viewport=Viewport(width=320, height=480),
                    )
                ]

    class Second(Component):
        citry = app
        template = """
            <p />
        """

        class Preview:
            enabled = True

    renderer = PreviewRenderer(ext)
    html = renderer.render_gallery().serialize(deps_strategy="document")
    assert html.count("<iframe") == 2
    assert "<script>bad</script>" not in html
    assert "<img src=x" not in html
    assert 'width="320"' in html
    assert 'height="480"' in html
    filtered = renderer.render_gallery(First.class_id).serialize(deps_strategy="document")
    assert filtered.count("<iframe") == 1
    assert Second.class_id not in filtered
    with pytest.raises(KeyError, match="Unknown"):
        renderer.render_gallery("unknown")


def test_empty_gallery_and_route_query_validation():
    _app_instance, ext = _app()
    renderer = PreviewRenderer(ext)
    assert "No component previews" in renderer.render_gallery().serialize()
    assert _route(renderer, "catalog").status == 200
    assert _route(renderer, "catalog", {"unused": ("x",)}).status == 400
    assert _route(renderer, "gallery", {"component": ("",)}).status == 400
    assert _route(renderer, "render/missing").status == 400
    assert _route(renderer, "render/missing", {"variant": ("one", "two")}).status == 400
    assert _route(renderer, "render/missing", {"variant": ("default",)}).status == 404
    response = _route(renderer, "catalog", method="HEAD")
    assert response.status == 200
    assert response.body == b""
    assert ("Cache-Control", "no-store") in response.headers
    assert _route(renderer, "catalog", method="POST").status == 405


def test_aliases_collapse_and_component_layout_rejects_other_engine():
    app, ext = _app()
    other, _ = _app()

    class Foreign(Component):
        citry = other
        template = """
            <c-slot name="content" />
        """

    class Example(Component):
        citry = app
        template = """
            <p />
        """

        class Preview:
            enabled = True
            page_layout = Layout(component=Foreign)

    app.register(Example, name="alias")
    assert len(ext.previews(Selection(names=("example", "alias")))) == 1
    with pytest.raises(PreviewError, match="belonging to this Citry"):
        _html(PreviewRenderer(ext), Example)


def test_inherited_file_and_layout_origins(tmp_path, monkeypatch):
    app, ext = _app()
    declaration = tmp_path / "author.py"
    declaration.write_text("# Declaration provenance fixture\n")
    (tmp_path / "example.html").write_text("<p>inherited file</p>")
    (tmp_path / "layout.html").write_text('<article><c-slot name="content" /></article>')

    class Parent(Component):
        citry = app
        template = """
            <p />
        """

        class Preview:
            template_file = "example.html"
            variant_layout = Layout(template_file="layout.html")

    class Child(Parent):
        pass

    # inspect.getfile is the provenance boundary; leave all rendering and file IO real.
    original = inspect.getfile
    monkeypatch.setattr(
        "citry.ext.preview.extension.inspect.getfile",
        lambda obj: str(declaration) if obj.__qualname__.endswith("Parent.Preview") else original(obj),
    )
    html = _html(PreviewRenderer(ext), Child)
    assert "<article" in html
    assert "inherited file</p>" in html


def test_broken_preview_returns_500_without_exposing_exception():
    app, ext = _app()

    class Broken(Component):
        citry = app
        template = """
            <p />
        """

        class Preview:
            template_file = "/does/not/exist/secret-example.html"

    response = _route(PreviewRenderer(ext), f"render/{Broken.class_id}", {"variant": ("default",)})
    assert response.status == 500
    assert "secret-example" not in response.content


def test_async_variants_rejected_without_creating_coroutine(recwarn):
    app, _ext = _app()
    with pytest.raises(ValueError, match=r"Preview\.variants must be an instance method"):

        class AsyncExample(Component):
            citry = app
            template = """
                <p>example</p>
            """

            class Preview:
                async def variants(self):
                    return [variant(slug="default", label="Default")]

    assert not recwarn.list


def test_component_key_error_is_render_failure():
    app, ext = _app()

    class Broken(Component):
        citry = app
        template = """
            <p>example</p>
        """

        class Preview:
            enabled = True

        def template_data(self, kwargs, slots):
            raise KeyError("private missing fixture")

    response = _route(PreviewRenderer(ext), f"render/{Broken.class_id}", {"variant": ("default",)})
    assert response.status == 500
    assert "private missing fixture" not in response.content


def test_none_template_alone_does_not_enable_preview():
    app, ext = _app()

    class Example(Component):
        citry = app
        template = """
            <p>ordinary</p>
        """

        class Preview:
            template = None

    assert ext.previews() == ()


@pytest.mark.parametrize("field", ["template", "template_file", "enabled", "variants"])
def test_global_defaults_reject_content_fields(field):
    with pytest.raises(ValueError, match="Unknown Preview field"):
        Citry(extensions=[PreviewExtension], extensions_defaults={"preview": {field: None}})


def test_template_globals_reach_child_through_layout_slot():
    app, ext = _app()

    class Consumer(Component):
        citry = app
        template = """
            <strong>{{ decorate(value) }}</strong>
        """

        def template_data(self, kwargs, slots):
            return {"value": self.inject("theme").value}

    class Example(Component):
        citry = app
        template = """
            <p>ordinary</p>
        """

        class Preview:
            template = """
                <c-consumer />
            """
            variant_layout = Layout(
                template="""
                    <c-provide key="theme" value="violet"><c-slot name="content" /></c-provide>
                """
            )

    html = _html(PreviewRenderer(ext), Example, template_globals={"decorate": lambda value: f"[{value}]"})
    assert "[violet]</strong>" in html


def test_explicit_effective_config_inheritance_does_not_author_default_variants():
    app, ext = _app()

    class Plain(Component):
        citry = app
        template = """
            <p>plain</p>
        """

    class Derived(Plain):
        class Preview(Plain.Preview):
            group = "Presentation only"

    assert ext.previews() == ()
    with pytest.raises(PreviewError, match="no enabled previews"):
        ext.previews(Selection(names=("derived",)))


def test_explicit_config_inheritance_keeps_default_layout_origin(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "page.html").write_text(
        '<html><head></head><body><main data-default-layout="yes"><c-slot name="content" /></main></body></html>'
    )
    app = Citry(
        extensions=[PreviewExtension],
        extensions_defaults={"preview": {"page_layout": Layout(template_file="page.html")}},
    )
    app.set_mounted_prefix("/citry")
    ext = app.extensions.get_extension("preview")

    class Plain(Component):
        citry = app
        template = """
            <p>plain</p>
        """

    class Derived(Plain):
        class Preview(Plain.Preview):
            enabled = True
            group = "Examples"

    html = _html(PreviewRenderer(ext), Derived)
    assert 'data-default-layout="yes"' in html
    assert "plain</p>" in html


def test_explicit_config_inheritance_retains_authored_template():
    app, ext = _app()

    class Parent(Component):
        citry = app
        template = """
            <p>ordinary</p>
        """

        class Preview:
            template = """
                <p>authored preview</p>
            """

    class Derived(Parent):
        class Preview(Parent.Preview):
            group = "Inherited example"

    assert {row.component for row in ext.previews()} == {Parent, Derived}
    html = _html(PreviewRenderer(ext), Derived)
    assert "authored preview</p>" in html
    assert "ordinary</p>" not in html


def test_simple_content_keeps_live_data_inside_an_ordinary_preview():
    app, ext = _app()
    calls = []

    class Probe(Component):
        citry = app
        simple = True
        template = """
            <p>{{ count }}</p>
        """

        @staticmethod
        def template_data(kwargs, slots):  # noqa: ARG004
            calls.append(None)
            return {"count": len(calls)}

    assert ">1</p>" in str(Probe())
    assert ">2</p>" in str(Probe())

    class Example(Component):
        citry = app
        template = """
            <c-probe />
        """

        class Preview:
            enabled = True

    assert ">3</p>" in _html(PreviewRenderer(ext), Example)
    assert ">4</p>" in _html(PreviewRenderer(ext), Example)


def test_simple_preview_configuration_is_rejected():
    app, _ext = _app()
    with pytest.raises(ValueError, match="simple=True but declares Preview"):

        class Example(Component):
            citry = app
            simple = True

            class Preview:
                enabled = True


def test_simple_preview_layout_rejects_named_content():
    app, ext = _app()

    class Frame(Component):
        citry = app
        simple = True
        template = """
            <c-slot />
        """

    class Example(Component):
        citry = app
        template = """
            <p>example</p>
        """

        class Preview:
            enabled = True
            variant_layout = Layout(component=Frame)

    with pytest.raises(TypeError, match="only default content"):
        _html(PreviewRenderer(ext), Example)
