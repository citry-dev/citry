"""Private worker snapshots keep schema policies current without freezing inline assets."""

from __future__ import annotations

import pytest

from citry import Citry, Component
from citry.analysis import python_class_resolution_signature
from citry_lsp import app_worker
from citry_lsp.project import load_project


@pytest.mark.parametrize(
    ("old", "new", "changes_schema"),
    [
        ("extra='forbid'", "extra='allow'", True),
        ("        title: str", "        title: str\n        added: int", True),
        ("class JsData(BaseModel):", "class JsData(dict):", True),
        ("<div></div>", "<article></article>", False),
        ("console.log(data.title)", "console.log(data.title, data.extra)", False),
    ],
)
def test_js_schema_snapshot_tracks_policy_fields_and_bases_but_not_inline_bodies(tmp_path, old, new, changes_schema):
    source = '''from citry import Citry, Component
from pydantic import BaseModel, ConfigDict
engine = Citry(autodiscover=False)
class Card(Component):
    citry = engine
    class JsData(BaseModel):
        model_config = ConfigDict(extra='forbid')
        title: str
    template = """
    <div></div>
    """
    js = """
    $component({ init({ data }) { console.log(data.title); } });
    """
'''
    app_file = tmp_path / "app.py"
    app_file.write_text(source, encoding="utf-8")
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready
    component = project.catalog.get_tag("c-card")
    chain = project.source_analysis.js_schema_resolution_chain(component)
    assert chain is not None
    owner = next(record for record in chain if record.source_file == app_file and record.qualname == "Card")
    assert python_class_resolution_signature(source, owner.qualname) == owner.resolution
    assert (
        python_class_resolution_signature(source.replace(old, new), owner.qualname) != owner.resolution
    ) is changes_schema


def test_js_schema_snapshot_includes_an_inherited_policy_only_base(tmp_path):
    schema_file = tmp_path / "schema.py"
    schema_file.write_text(
        """from pydantic import BaseModel, ConfigDict
class Policy(BaseModel):
    model_config = ConfigDict(extra='forbid')
""",
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text(
        '''from citry import Citry, Component
from schema import Policy
engine = Citry(autodiscover=False)
class Card(Component):
    citry = engine
    class JsData(Policy):
        title: str
    template = """
    <div></div>
    """
''',
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready
    chain = project.source_analysis.js_schema_resolution_chain(project.catalog.get_tag("c-card"))
    assert chain is not None
    policy = next(record for record in chain if record.source_file == schema_file)
    source = schema_file.read_text(encoding="utf-8")
    assert python_class_resolution_signature(source, policy.qualname) == policy.resolution
    assert python_class_resolution_signature(source.replace("forbid", "allow"), policy.qualname) != policy.resolution


@pytest.mark.parametrize(
    ("child_state", "includes_parent_base"),
    [
        # A plain State replaces the parent's, so the parent's base class
        # can no longer change Card's fields.
        ("    class State:\n        own: int\n", False),
        # Naming the parent's State as a base keeps its fields, so its own
        # module-level base still has to be checked for edits.
        ("    class State(Parent.State):\n        own: int\n", True),
        # Declaring nothing keeps the parent's State itself.
        ("    pass\n", True),
    ],
)
def test_state_snapshot_follows_only_the_nearest_declaration(tmp_path, child_state, includes_parent_base):
    fields_file = tmp_path / "fields.py"
    fields_file.write_text("class ParentFields:\n    inherited: str = ''\n", encoding="utf-8")
    (tmp_path / "app.py").write_text(
        "from citry import Citry, Component\n"
        "from fields import ParentFields\n"
        "engine = Citry(autodiscover=False)\n"
        "class Parent(Component):\n"
        "    citry = engine\n"
        "    template = '<div></div>'\n"
        "    class State(ParentFields):\n"
        "        pass\n"
        "class Card(Parent):\n"
        f"{child_state}",
        encoding="utf-8",
    )
    project = load_project(tmp_path, "app:engine")
    assert project.status.registry_ready
    chain = project.source_analysis.state_resolution_chain(project.catalog.get_tag("c-card"))
    assert chain is not None
    assert any(record.source_file == fields_file for record in chain) is includes_parent_base


def test_state_snapshot_is_withheld_when_the_runtime_rejects_the_declaration(monkeypatch):
    engine = Citry(autodiscover=False)

    class Card(Component):
        citry = engine
        template = "<div></div>"

    def reject(component_class, name):
        # The runtime raises ValueError for conflicting bases or a non-class
        # binding; such a class can only reach the worker through a stub.
        raise ValueError(name)

    monkeypatch.setattr(app_worker, "_nearest_data_shape_declaration", reject)

    assert app_worker._schema_resolution_chain(Card, engine, "State") is None
