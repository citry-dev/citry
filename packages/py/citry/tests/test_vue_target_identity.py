from __future__ import annotations

import pytest

from citry import Citry, Component
from citry._vue.capture import render_prepared_direct
from citry._vue.direct_capture import assemble_typed_render
from citry._vue.prepared import PreparedDefinition, PreparedOccurrence, PreparedView
from citry._vue.protocol import DefinitionAsset, prepared_manifest


def _assembly(component: Component, *, root_id: str | None = None):
    return assemble_typed_render(
        render_prepared_direct(component),
        revision=0,
        root_occurrence_id=root_id,
        tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-"),
    )


def test_python_composition_uses_physical_parent_local_placement_identity() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Leaf(Component):
        citry = registry
        template = "<i>leaf</i>"

    class Target(Component):
        citry = registry
        template = "<section>{{ first }}{{ second }}</section>"

        def template_data(self, kwargs, slots):
            return {"first": Leaf(), "second": Leaf()}

    class Page(Component):
        citry = registry
        template = "<main>{{ before }}{{ target }}{{ after }}</main>"

        def template_data(self, kwargs, slots):
            return {"before": Leaf(), "target": Target(), "after": Leaf()}

    whole = _assembly(Page()).view
    target = next(item for item in whole.occurrences if item.type_key == Target.class_id)
    whole_children = [item for item in whole.occurrences if item.parent_id == target.id]

    isolated = _assembly(Target(), root_id=target.id).view
    isolated_children = [item for item in isolated.occurrences if item.parent_id == target.id]

    assert [(item.id, item.placement_key) for item in isolated_children] == [
        (item.id, item.placement_key) for item in whole_children
    ]
    assert len({item.placement_key for item in whole_children}) == 2


def test_authored_keyed_reorder_keeps_placement_keys_with_items() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Row(Component):
        citry = registry
        template = "<p>{{ value }}</p>"

        def template_data(self, kwargs, slots):
            return kwargs

    class Rows(Component):
        citry = registry
        template = '<c-for each="value in values"><c-Row #c-key="value" c-value="value" /></c-for>'

        def template_data(self, kwargs, slots):
            return kwargs

    def keyed(values: list[str]) -> dict[str, tuple[str, str | None]]:
        view = _assembly(Rows(values=values)).view
        root = next(item for item in view.occurrences if item.id == view.root_id)
        child_ids = next(iter(root.prepared_data["callRuns"].values()))
        children = {item.id: item for item in view.occurrences if item.type_key == Row.class_id}
        return {
            value: (child_id, children[child_id].placement_key)
            for value, child_id in zip(values, child_ids, strict=True)
        }

    assert keyed(["a", "b"]) == keyed(["b", "a"])


def test_supplied_slot_child_placement_uses_physical_receiver() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Leaf(Component):
        citry = registry
        template = "<b>leaf</b>"

    class Receiver(Component):
        citry = registry
        template = '<article><c-slot name="body" /></article>'

    class Caller(Component):
        citry = registry
        template = (
            '<c-Receiver #c-key="\'receiver\'"><c-fill name="body"><c-Leaf #c-key="\'leaf\'" /></c-fill></c-Receiver>'
        )

    view = _assembly(Caller()).view
    caller = next(item for item in view.occurrences if item.type_key == Caller.class_id)
    receiver = next(item for item in view.occurrences if item.type_key == Receiver.class_id)
    leaf = next(item for item in view.occurrences if item.type_key == Leaf.class_id)

    assert receiver.parent_id == caller.id
    assert leaf.parent_id == receiver.id
    assert leaf.placement_key


def test_assembly_exposes_one_canonical_render_identity_per_occurrence() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Child(Component):
        citry = registry
        template = "<p>child</p>"

    class Root(Component):
        citry = registry
        template = "<main><c-Child /></main>"

    assembly = _assembly(Root())
    occurrence_ids = {item.id for item in assembly.view.occurrences}

    assert set(assembly.occurrence_to_render) == occurrence_ids
    assert len(set(assembly.occurrence_to_render.values())) == len(occurrence_ids)
    assert {
        assembly.render_to_occurrence[render_id] for render_id in assembly.occurrence_to_render.values()
    } == occurrence_ids


def test_selected_transparent_root_has_its_own_canonical_render_identity() -> None:
    registry = Citry(autodiscover=False, extensions=[])

    class Transparent(Component):
        citry = registry
        transparent = True
        template = "<strong>transparent</strong>"

    rendered = render_prepared_direct(Transparent())
    assembly = assemble_typed_render(
        rendered, revision=0, tag_for_type=lambda type_key: "x-" + type_key.lower().replace("_", "-")
    )

    assert assembly.occurrence_to_render == {
        assembly.view.root_id: rendered.context.component.id,
    }


def test_occurrence_placement_contract_and_wire_shape() -> None:
    root_definition = PreparedDefinition("root-def", "Root", ())
    root = PreparedOccurrence("root", "Root", "root-def", {}, {}, None, None)
    view = PreparedView(0, "root", (root,), (root_definition,))
    asset = DefinitionAsset("root-def", "/vue/" + "a" * 64 + ".js", "a" * 64, "ordinary-vnodes/1", "b" * 64, (), ())

    assert prepared_manifest(app_id="app", view=view, assets=(asset,))["occurrences"][0]["placementKey"] is None
    with pytest.raises(ValueError, match="root occurrence must not have a placement key"):
        PreparedOccurrence("root", "Root", "root-def", {}, {}, None, "root-key")
    with pytest.raises(TypeError, match="occurrence placement key"):
        PreparedOccurrence("child", "Child", "child-def", {}, {}, "root", None)

    duplicate_children = (
        root,
        PreparedOccurrence("first", "Child", "child-def", {}, {}, "root", "same"),
        PreparedOccurrence("second", "Child", "child-def", {}, {}, "root", "same"),
    )
    with pytest.raises(ValueError, match="duplicate prepared occurrence placement key"):
        PreparedView(
            0,
            "root",
            duplicate_children,
            (root_definition, PreparedDefinition("child-def", "Child", ())),
        )
