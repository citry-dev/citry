"""Private worker snapshots keep schema policies current without freezing inline assets."""

from __future__ import annotations

import pytest

from citry.analysis import python_class_resolution_signature
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
