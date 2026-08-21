"""Falsifier tests for engine-neutral component library publication."""

from __future__ import annotations

import ast
import gc
import inspect
import threading
from dataclasses import is_dataclass
from pathlib import Path
from types import ModuleType
from typing import get_type_hints
from weakref import ref

import pytest

import citry.library_component as library_component_module
from citry import (
    AlreadyRegistered,
    Citry,
    CitryElement,
    CitryLifecycleInProgress,
    CitryRender,
    Component,
    ComponentLibrary,
    ComponentLike,
    Extension,
    LibraryComponent,
    LibraryComponentContextError,
    LibraryComponentInvocation,
    LibraryInstallationStale,
    LibraryManifestChanged,
    LibraryNotInstalled,
)


def test_definition_is_inert_and_call_defensively_copies_inputs():
    app = Citry(autodiscover=False)

    class CButton(LibraryComponent):
        template = "button"

    kwargs = {"label": "Save"}
    slots = {"default": "body"}
    invocation = CButton(**kwargs, slots=slots)
    kwargs["label"] = "Changed"
    slots["default"] = "changed"

    assert isinstance(invocation, LibraryComponentInvocation)
    assert isinstance(invocation, ComponentLike)
    assert dict(invocation.kwargs) == {"label": "Save"}
    assert dict(invocation.slots) == {"default": "body"}
    assert not app.has("cbutton")
    assert not app.has("c-button")


def test_slots_are_a_reserved_mapping_and_contextless_render_is_focused():
    class CButton(LibraryComponent):
        template = "button"

    with pytest.raises(TypeError, match="slots must be a mapping"):
        CButton(slots=["not", "a", "mapping"])

    invocation = CButton()
    with pytest.raises(LibraryComponentContextError, match="requires a Citry instance"):
        invocation.render()
    with pytest.raises(LibraryComponentContextError, match="requires a Citry instance"):
        str(invocation)


def test_manifest_installation_supports_python_and_template_composition():
    app = Citry(autodiscover=False)

    class CButton(LibraryComponent):
        class Kwargs:
            label: str

        class Slots:
            default: object = ""

        template = "<button>{{ label }}<c-slot /></button>"

        def template_data(self, kwargs, slots):
            return {"label": kwargs.label}

    manifest = ComponentLibrary(name="test-ui", components=(CButton,))
    installation = app.register_library(manifest)
    concrete = installation.component(CButton)

    assert str(CButton(label="Save", slots={"default": "!"}).render(citry=app)) == (
        '<button data-cid-c1="">Save!</button>'
    )
    assert app.get("CButton") is concrete
    assert app.get("c-button") is concrete

    class Page(Component):
        citry = app
        template = "<main>{{ button }}</main>"

        def template_data(self, kwargs, slots):
            return {"button": CButton(label="Open")}

    assert str(Page()) == '<main data-cid-c2=""><button data-cid-c3="">Open</button></main>'


def test_library_invocation_forwards_explicit_root_provides():
    app = Citry(autodiscover=False)
    marker = object()
    seen = {}

    class CReader(LibraryComponent):
        def template_data(self, kwargs, slots):
            seen["marker"] = self.inject("request_scope")
            return {}

        template = """
            ready
        """

    app.register_library(ComponentLibrary(name="readers", components=(CReader,)))

    rendered = CReader().render(
        citry=app,
        provides={"request_scope": marker},
    )

    assert str(rendered).strip() == "ready"
    assert seen["marker"] is marker


def test_module_manifest_and_repeat_registration_return_exact_installation():
    app = Citry(autodiscover=False)

    class CNotice(LibraryComponent):
        template = "notice"

    manifest = ComponentLibrary(name="notices", components=(CNotice,))
    package = ModuleType("notices")
    package.__citry_library__ = manifest

    first = app.register_library(package)
    second = app.register_library(ComponentLibrary(name="notices", components=(CNotice,)))

    assert second is first
    assert app.get_library_installation("notices") is first
    assert first.definitions == (CNotice,)
    assert first[CNotice] is first.component(CNotice)


def test_two_engines_receive_distinct_classes_with_stable_logical_identity():
    class CNotice(LibraryComponent):
        template = "notice"

    manifest = ComponentLibrary(name="notices", components=(CNotice,))
    left = Citry(autodiscover=False)
    right = Citry(autodiscover=False)

    LeftNotice = left.register_library(manifest)[CNotice]
    RightNotice = right.register_library(manifest)[CNotice]

    assert LeftNotice is not RightNotice
    assert LeftNotice.citry is left
    assert RightNotice.citry is right
    assert LeftNotice.class_id == RightNotice.class_id
    assert LeftNotice.definition_id != RightNotice.definition_id
    assert LeftNotice.__module__ == CNotice.__module__
    assert LeftNotice.__qualname__ == CNotice.__qualname__


def test_definition_inheritance_zero_argument_super_and_schemas_survive():
    app = Citry(autodiscover=False)

    class ControlBase(LibraryComponent):
        class Kwargs:
            label: str

        def template_data(self, kwargs, slots):
            return {"text": kwargs.label}

    class CFancyControl(ControlBase):
        class Kwargs:
            suffix: str = "!"

        template = "{{ text }}{{ suffix }}"

        def template_data(self, kwargs, slots):
            return {**super().template_data(kwargs, slots), "suffix": kwargs.suffix}

    concrete = app.register_library(ComponentLibrary("controls", (CFancyControl,)))[CFancyControl]

    assert str(CFancyControl(label="Go").render(citry=app)) == "Go!"
    assert tuple(concrete.Kwargs.__dataclass_fields__) == ("label", "suffix")
    assert concrete.__mro__[:4] == (concrete, CFancyControl, ControlBase, LibraryComponent)

    class BrandedControl(concrete):
        name = "BrandedControl"

    assert BrandedControl.citry is app
    assert str(BrandedControl(label="Run")) == "Run!"


def test_pure_library_definition_requires_an_explicit_per_class_promise():
    app = Citry(autodiscover=False)

    class PureBase(LibraryComponent):
        pure = True

    class CLeaf(PureBase):
        template = "leaf"

    assert PureBase.pure is True
    assert CLeaf.pure is False
    CLeaf.pure = True
    assert CLeaf.pure is True

    with pytest.raises(ValueError, match="pure must be an exact bool"):
        CLeaf.pure = 1  # type: ignore[assignment]
    with pytest.raises(AttributeError, match="set it to False"):
        del CLeaf.pure

    concrete = app.register_library(ComponentLibrary("pure-library", (CLeaf,)))[CLeaf]
    assert concrete.pure is True


def test_separately_installed_parent_and_child_keep_authored_not_concrete_inheritance():
    app = Citry(autodiscover=False)

    class CBase(LibraryComponent):
        template = "base"

    class CChild(CBase):
        template = "child"

    installed = app.register_library(ComponentLibrary("inheritance", (CBase, CChild)))

    assert issubclass(installed[CChild], CBase)
    assert not issubclass(installed[CChild], installed[CBase])


def test_primary_files_resolve_beside_the_inert_definition_module():
    app = Citry(autodiscover=False)

    class CFileNotice(LibraryComponent):
        class Kwargs:
            label: str

        template_file = "fixtures/library_component.html"
        js_file = "fixtures/library_component.js"
        css_file = "fixtures/library_component.css"

        def template_data(self, kwargs, slots):
            return {"label": kwargs.label}

    concrete = app.register_library(ComponentLibrary("file-notices", (CFileNotice,)))[CFileNotice]

    assert '<p data-cid-c1="">From file</p>' in str(CFileNotice(label="From file").render(citry=app))
    assert concrete.get_js() == 'console.log("library component");\n'
    assert concrete.get_css() == ".library-component { color: blue; }\n"
    info = app.inspect_component(concrete, resolve_assets=True)
    assert info.import_path == f"{CFileNotice.__module__}.{CFileNotice.__qualname__}"
    assert info.description is None
    assert info.assets.template.declared_on == info.import_path
    assert info.assets.template.resolved_path is not None
    assert info.assets.template.resolved_path.as_posix().endswith("tests/fixtures/library_component.html")


def test_complete_manifest_allows_forward_and_circular_template_references():
    app = Citry(autodiscover=False)

    class CAlpha(LibraryComponent):
        template = "<c-CBeta />"

    class CBeta(LibraryComponent):
        template = '<c-if cond="False"><c-CAlpha /></c-if><span>beta</span>'

    installed = app.register_library(ComponentLibrary("circular", (CAlpha, CBeta)))

    assert installed[CAlpha].get_template() is not None
    assert installed[CBeta].get_template() is not None
    assert str(CAlpha().render(citry=app)) == '<span data-cid-c2="" data-cid-c1="">beta</span>'


def test_custom_extension_declaration_is_materialized_per_engine():
    class ThemeExtension(Extension):
        name = "theme"

    class CBadge(LibraryComponent):
        class Theme:
            tone = "strong"

        template = "badge"

    manifest = ComponentLibrary("badges", (CBadge,), required_extensions=("theme",))
    left = Citry(extensions=(ThemeExtension,), autodiscover=False)
    right = Citry(extensions=(ThemeExtension,), autodiscover=False)

    LeftBadge = left.register_library(manifest)[CBadge]
    RightBadge = right.register_library(manifest)[CBadge]

    assert LeftBadge.Theme.tone == "strong"
    assert RightBadge.Theme.tone == "strong"
    assert LeftBadge.Theme is not RightBadge.Theme


def test_builtin_state_events_cache_and_dependencies_follow_normal_component_lifecycle():
    app = Citry(autodiscover=False)

    class CInteractive(LibraryComponent):
        class State:
            count: int = 0

        class Events:
            def increment(self):
                return None

        class Cache:
            enabled = True
            version = "interactive-v1"

        class Dependencies:
            js = ["/static/interactive.js"]

        template = "interactive"

    concrete = app.register_library(ComponentLibrary("interactive", (CInteractive,)))[CInteractive]
    events = app.extensions.get_extension("events").resolve(concrete)
    cache_info = app.inspect_component(concrete, include_extensions=("cache",)).extensions[0]

    assert is_dataclass(concrete.State)
    assert concrete.State().count == 0
    assert tuple(events.handlers) == ("increment",)
    assert dict(cache_info.data)["enabled"] is True
    assert concrete.get_dependencies().js == ("/static/interactive.js",)


def test_missing_required_extension_fails_before_component_hooks():
    seen = []

    class Observer(Extension):
        name = "observer"

        def on_component_class_created(self, ctx):
            seen.append(ctx.component_class)

    app = Citry(extensions=(Observer,), autodiscover=False)

    class CBadge(LibraryComponent):
        template = "badge"

    manifest = ComponentLibrary("badges", (CBadge,), required_extensions=("missing",))
    with pytest.raises(ValueError, match="required extension 'missing'"):
        app.register_library(manifest)

    assert seen == []
    assert not app.has("cbadge")


def test_manifest_rejects_duplicate_aliases_reserved_names_and_identities():
    class FooBar(LibraryComponent):
        template = "one"

    class Foobar(LibraryComponent):
        template = "two"

    with pytest.raises(ValueError, match="both claim registry name 'foobar'"):
        ComponentLibrary("duplicates", (FooBar, Foobar))

    class Cache(LibraryComponent):
        template = "reserved"

    with pytest.raises(ValueError, match="reserved name 'cache'"):
        ComponentLibrary("reserved", (Cache,))

    DuplicateFooBar = type(
        "FooBar",
        (LibraryComponent,),
        {"__module__": FooBar.__module__, "__qualname__": FooBar.__qualname__, "template": "duplicate"},
    )
    with pytest.raises(ValueError, match="duplicate definition identity"):
        ComponentLibrary("identities", (FooBar, DuplicateFooBar))


@pytest.mark.parametrize("value", ["abc", b"abc", {"one", "two"}, {"one": "two"}])
def test_manifest_rejects_non_sequence_or_string_collections(value):
    class CNotice(LibraryComponent):
        template = "notice"

    with pytest.raises(TypeError, match="ordered, non-string sequence"):
        ComponentLibrary("invalid-components", value)
    with pytest.raises(TypeError, match="ordered, non-string sequence"):
        ComponentLibrary("invalid-extensions", (CNotice,), required_extensions=value)


def test_public_library_annotations_resolve_at_runtime():
    from citry.library_component import LibraryComponentMeta, LibraryInstallation

    class CNotice(LibraryComponent):
        template = "notice"

    protocol_hints = get_type_hints(ComponentLike.__citry_element__)
    resolve_hints = get_type_hints(LibraryComponentInvocation.resolve)
    render_hints = get_type_hints(LibraryComponentInvocation.render)
    installation_hints = get_type_hints(LibraryInstallation)
    call_hints = get_type_hints(LibraryComponentMeta.__call__)
    registration_hints = get_type_hints(Citry.register_library)

    assert protocol_hints == {"citry": Citry, "return": CitryElement}
    assert resolve_hints["citry"] is Citry
    assert resolve_hints["return"] is CitryElement
    assert render_hints["return"] is CitryRender
    assert installation_hints["library"] is ComponentLibrary
    assert call_hints["return"] is LibraryComponentInvocation
    assert registration_hints["library"] == ComponentLibrary | ModuleType
    assert registration_hints["return"].__name__ == "LibraryInstallation"
    assert inspect.signature(CNotice).return_annotation == "LibraryComponentInvocation"


def test_preflight_registry_collision_constructs_no_library_classes():
    created = []

    class Observer(Extension):
        name = "observer"

        def on_component_class_created(self, ctx):
            created.append(ctx.component_class)

    app = Citry(extensions=(Observer,), autodiscover=False)

    class CFirst(LibraryComponent):
        template = "first"

    class CSecond(LibraryComponent):
        template = "second"

    class Occupied(Component):
        citry = app
        name = "csecond"
        template = "occupied"

    created.clear()
    with pytest.raises(AlreadyRegistered, match="registry name 'csecond'"):
        app.register_library(ComponentLibrary("collision", (CFirst, CSecond)))

    assert created == []
    assert not app.has("cfirst")
    assert app.get("csecond") is Occupied


@pytest.mark.parametrize("failure", [RuntimeError("rejected"), KeyboardInterrupt()])
@pytest.mark.parametrize(
    ("reject_name", "registered_names"),
    [
        ("CFirst", []),
        ("CSecond", ["CFirst"]),
        ("CThird", ["CFirst", "CSecond"]),
    ],
)
def test_hook_failure_rolls_back_every_class_and_installation_without_compensation(
    failure,
    reject_name,
    registered_names,
):
    registered = []
    unregistered = []

    class RejectComponent(Extension):
        name = "reject_component"

        def on_component_class_created(self, ctx):
            if ctx.component_class.__name__ == reject_name:
                raise failure

        def on_component_registered(self, ctx):
            registered.append(ctx.component_class)

        def on_component_unregistered(self, ctx):
            unregistered.append(ctx.component_class)

    app = Citry(extensions=(RejectComponent,), autodiscover=False)

    class CFirst(LibraryComponent):
        template = "first"

    class CSecond(LibraryComponent):
        template = "second"

    class CThird(LibraryComponent):
        template = "third"

    with pytest.raises(type(failure), match="rejected" if isinstance(failure, RuntimeError) else None):
        app.register_library(ComponentLibrary("rollback", (CFirst, CSecond, CThird)))

    assert [item.__name__ for item in registered] == registered_names
    assert unregistered == []
    assert not app.has("cfirst")
    assert not app.has("csecond")
    assert not app.has("cthird")
    with pytest.raises(LibraryNotInstalled):
        app.get_library_installation("rollback")


def test_hook_failure_removes_files_loaded_by_rolled_back_classes():
    retained = []

    class LoadThenReject(Extension):
        name = "load_then_reject"

        def on_component_class_created(self, ctx):
            retained.append(ctx.component_class)
            if ctx.component_class.__name__ == "CFirst":
                ctx.component_class.get_template()
            if ctx.component_class.__name__ == "CSecond":
                raise RuntimeError("reject after file load")

    app = Citry(extensions=(LoadThenReject,), autodiscover=False)

    class CFirst(LibraryComponent):
        template_file = "fixtures/library_component.html"

    class CSecond(LibraryComponent):
        template = "second"

    with pytest.raises(RuntimeError, match="reject after file load"):
        app.register_library(ComponentLibrary("file-rollback", (CFirst, CSecond)))

    fixture = Path(__file__).parent / "fixtures" / "library_component.html"
    assert retained
    assert app.get_components_for_file(fixture) == []


def test_hook_created_auxiliary_component_is_part_of_outer_rollback():
    class CreateThenReject(Extension):
        name = "create_then_reject"

        def on_component_class_created(self, ctx):
            if ctx.component_class.__name__ == "CFirst":

                class Auxiliary(Component):
                    citry = self.citry
                    template = "auxiliary"

            if ctx.component_class.__name__ == "CSecond":
                raise RuntimeError("reject after auxiliary")

    app = Citry(extensions=(CreateThenReject,), autodiscover=False)

    class CFirst(LibraryComponent):
        template = "first"

    class CSecond(LibraryComponent):
        template = "second"

    with pytest.raises(RuntimeError, match="reject after auxiliary"):
        app.register_library(ComponentLibrary("auxiliary-rollback", (CFirst, CSecond)))

    assert not app.has("auxiliary")
    assert not app.has("cfirst")
    assert not app.has("csecond")


def test_recursive_registration_rejects_and_rolls_back_outer_installation():
    manifest_holder = {}

    class Recurse(Extension):
        name = "recurse"

        def on_component_class_created(self, ctx):
            if ctx.component_class.__name__ == "CNotice":
                self.citry.register_library(manifest_holder["manifest"])

    app = Citry(extensions=(Recurse,), autodiscover=False)

    class CNotice(LibraryComponent):
        template = "notice"

    manifest = ComponentLibrary("recursive", (CNotice,))
    manifest_holder["manifest"] = manifest

    with pytest.raises(RuntimeError, match="cannot run recursively"):
        app.register_library(manifest)
    assert not app.has("cnotice")
    with pytest.raises(LibraryNotInstalled):
        app.get_library_installation("recursive")


def test_concurrent_readers_fail_fast_until_installation_commits():
    entered = threading.Event()
    release = threading.Event()

    class Pause(Extension):
        name = "pause"

        def on_component_class_created(self, ctx):
            entered.set()
            assert release.wait(timeout=5)

    app = Citry(extensions=(Pause,), autodiscover=False)

    class CNotice(LibraryComponent):
        template = "notice"

    manifest = ComponentLibrary("concurrent", (CNotice,))
    result = []
    errors = []

    def install():
        try:
            result.append(app.register_library(manifest))
        except Exception as error:  # noqa: BLE001  # pragma: no cover - assertion reports the captured error
            errors.append(error)

    worker = threading.Thread(target=install)
    worker.start()
    assert entered.wait(timeout=5)
    try:
        with pytest.raises(CitryLifecycleInProgress):
            app.get("cnotice")
        with pytest.raises(CitryLifecycleInProgress):
            app.has("cnotice")
        with pytest.raises(CitryLifecycleInProgress):
            app.get_library_installation("concurrent")
        with pytest.raises(CitryLifecycleInProgress):
            app.register_library(manifest)
    finally:
        release.set()
        worker.join(timeout=5)

    assert not worker.is_alive()
    assert errors == []
    assert len(result) == 1
    assert app.register_library(manifest) is result[0]


def test_changed_or_reloaded_manifest_is_rejected_while_active():
    app = Citry(autodiscover=False)

    class CNotice(LibraryComponent):
        template = "old"

    old_invocation = CNotice()
    first = app.register_library(ComponentLibrary("notices", (CNotice,)))
    stable_class_id = first[CNotice].class_id

    CReloadedNotice = type(
        "CNotice",
        (LibraryComponent,),
        {"__module__": CNotice.__module__, "__qualname__": CNotice.__qualname__, "template": "new"},
    )
    with pytest.raises(LibraryManifestChanged, match="definition generation"):
        app.register_library(ComponentLibrary("notices", (CReloadedNotice,)))

    app.clear()
    reloaded = app.register_library(ComponentLibrary("notices", (CReloadedNotice,)))
    assert str(CReloadedNotice().render(citry=app)) == "new"
    assert reloaded[CReloadedNotice].class_id == stable_class_id
    with pytest.raises(LibraryNotInstalled):
        old_invocation.render(citry=app)


def test_clear_retires_invocations_and_handles_then_reinstall_creates_fresh_generation():
    app = Citry(autodiscover=False)

    class CNotice(LibraryComponent):
        template = "notice"

    manifest = ComponentLibrary("notices", (CNotice,))
    invocation = CNotice()
    first = app.register_library(manifest)
    FirstNotice = first[CNotice]
    first_definition_id = FirstNotice.definition_id
    class_id = FirstNotice.class_id

    app.clear()

    assert not first.is_active
    with pytest.raises(LibraryInstallationStale, match="no longer active"):
        first.component(CNotice)
    with pytest.raises(LibraryNotInstalled, match="not installed"):
        invocation.render(citry=app)

    second = app.register_library(manifest)
    SecondNotice = second[CNotice]
    assert second is not first
    assert SecondNotice is not FirstNotice
    assert SecondNotice.class_id == class_id
    assert SecondNotice.definition_id != first_definition_id
    assert str(invocation.render(citry=app)) == "notice"
    assert str(FirstNotice()) == "notice"


def test_cleared_concrete_class_is_collectible_without_retained_handles():
    app = Citry(autodiscover=False)

    class CNotice(LibraryComponent):
        template = "notice"

    installation = app.register_library(ComponentLibrary("notices", (CNotice,)))
    concrete_ref = ref(installation[CNotice])
    app.clear()
    del installation
    gc.collect()

    assert concrete_ref() is None


def test_manifest_seals_public_definition_fields_after_decorators_can_finish():
    class CNotice(LibraryComponent):
        template = "notice"

    CNotice.decorated = True
    ComponentLibrary("notices", (CNotice,))

    with pytest.raises(AttributeError, match="published library component"):
        CNotice.template = "changed"
    with pytest.raises(AttributeError, match="published library component"):
        del CNotice.decorated


def test_direct_component_mixing_is_rejected_with_registration_guidance():
    class CNotice(LibraryComponent):
        template = "notice"

    with pytest.raises(TypeError, match=r"Citry\.register_library"):

        class BoundNotice(CNotice, Component):
            pass


def test_unrelated_same_name_never_satisfies_a_retained_invocation():
    app = Citry(autodiscover=False)

    class CNotice(LibraryComponent):
        template = "library"

    invocation = CNotice()

    class CNotice(Component):
        citry = app
        template = "unrelated"

    with pytest.raises(LibraryNotInstalled, match="register_library"):
        invocation.render(citry=app)


def test_manifest_owned_names_cannot_be_individually_unregistered():
    app = Citry(autodiscover=False)

    class CNotice(LibraryComponent):
        template = "notice"

    concrete = app.register_library(ComponentLibrary("notices", (CNotice,)))[CNotice]

    with pytest.raises(ValueError, match="library-managed component"):
        app.unregister("cnotice")
    with pytest.raises(ValueError, match="library-managed component"):
        app.unregister(concrete)
    assert app.get("cnotice") is concrete


def test_library_root_cannot_be_called_or_published():
    assert not issubclass(LibraryComponent, Component)
    assert not hasattr(LibraryComponent, "get_template")
    with pytest.raises(TypeError, match="abstract publishing base"):
        LibraryComponent()
    with pytest.raises(TypeError, match="definition classes"):
        ComponentLibrary("invalid", (LibraryComponent,))


def test_checker_only_authoring_base_declares_every_public_component_field():
    # The base exists only to static checkers, so compare its source annotations
    # with the live Component annotations rather than importing the nested class.
    source = Path(library_component_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    authoring_base = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "_LibraryComponentAuthoringBase"
    )
    authoring_fields = {
        node.target.id
        for node in authoring_base.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and not node.target.id.startswith("_")
    }
    authoring_fields.update(
        node.name
        for node in authoring_base.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(isinstance(decorator, ast.Name) and decorator.id == "property" for decorator in node.decorator_list)
        and not node.name.startswith("_")
    )
    component_fields = {name for name in Component.__annotations__ if not name.startswith("_")}
    component_fields.update(name for name, value in Component.__dict__.items() if isinstance(value, property))

    assert authoring_fields == component_fields
