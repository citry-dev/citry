"""The trust-boundary validator reports a hook, action, or security setting that the design doc does not name."""

from pathlib import Path

from scripts.validators import trust_boundary_rows

_EXTENSION = """
class Extension:
    def on_serialize(self, ctx): ...
    def urls(self): ...
    def _private_helper(self): ...
"""
_ACTIONS = '__all__ = ["Action", "Redirect"]\n'
_SETTINGS = """
class CitrySettings:
    sandbox_expressions: bool = True
    security_csp: str = "off"
"""
# A hook fired by name; the docstring example must not count as a hook.
_DISPATCHER = '''
def dispatch(manager, ctx):
    """Call `manager.emit("on_my_event", ctx)` to fire your own hook."""
    return manager.emit("on_event", ctx, result="first")
'''
_DISPATCHER_MODULE = trust_boundary_rows.PACKAGE_DIR / "ext/events/dispatcher.py"
_DOC = "Rows for `on_serialize()`, `Extension.urls`, `on_event`, `Redirect(url=)` and `security_csp`.\n"


def _repository(
    tmp_path: Path,
    *,
    doc: str = _DOC,
    extension: str = _EXTENSION,
    settings: str = _SETTINGS,
    dispatcher: str = _DISPATCHER,
) -> Path:
    # Lay out every file the validator reads, all consistent, so each test
    # changes exactly one of them.
    files = {
        trust_boundary_rows.DOC: doc,
        trust_boundary_rows.EXTENSION_MODULE: extension,
        trust_boundary_rows.ACTIONS_MODULE: _ACTIONS,
        trust_boundary_rows.SETTINGS_MODULE: settings,
        _DISPATCHER_MODULE: dispatcher,
    }
    for relative, text in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def test_a_doc_naming_every_input_passes(tmp_path: Path) -> None:
    assert trust_boundary_rows.check(_repository(tmp_path)) == []


def test_a_new_hook_without_a_row_is_reported(tmp_path: Path) -> None:
    root = _repository(tmp_path, extension=_EXTENSION + "    def on_new_output(self, ctx): ...\n")

    problems = trust_boundary_rows.check(root)

    assert len(problems) == 1
    assert "extension hook `on_new_output`" in problems[0]


def test_a_name_outside_a_code_span_does_not_count(tmp_path: Path) -> None:
    # Plain prose that mentions the name is not a row; the base class
    # `Action` is skipped on purpose.
    root = _repository(tmp_path, doc=_DOC.replace("`Redirect(url=)`", "Redirect"))

    problems = trust_boundary_rows.check(root)

    assert len(problems) == 1
    assert "Events action `Redirect`" in problems[0]


def test_a_source_that_changed_shape_is_reported(tmp_path: Path) -> None:
    # Without this, renaming the class would make the check pass silently.
    root = _repository(tmp_path, extension="class Renamed:\n    def on_serialize(self): ...\n")

    problems = trust_boundary_rows.check(root)

    assert problems == [
        f"found no extension hook names in {trust_boundary_rows.EXTENSION_MODULE}; update trust_boundary_rows.py"
    ]


def test_a_hook_fired_by_name_without_a_row_is_reported(tmp_path: Path) -> None:
    root = _repository(tmp_path, doc=_DOC.replace("`on_event`", "on_event"))

    problems = trust_boundary_rows.check(root)

    assert len(problems) == 1
    assert "extension hook `on_event` (fired by name" in problems[0]


def test_a_new_security_setting_without_a_row_is_reported(tmp_path: Path) -> None:
    root = _repository(tmp_path, settings=_SETTINGS + '    security_new: str = "off"\n')

    problems = trust_boundary_rows.check(root)

    assert len(problems) == 1
    assert "security setting `security_new`" in problems[0]


def test_a_package_with_no_named_hooks_is_reported(tmp_path: Path) -> None:
    # Renaming `emit` would otherwise leave every named hook unchecked.
    root = _repository(tmp_path, dispatcher="def dispatch(manager, ctx):\n    return manager.fire('on_event', ctx)\n")

    problems = trust_boundary_rows.check(root)

    assert len(problems) == 1
    assert problems[0].startswith("found no hooks fired by name")
