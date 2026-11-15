"""
``citry._lsp_support`` keeps its names and signatures for all of citry 1.x.

citry-lsp imports Citry's internals only through this module, and an
installed citry-lsp 1.x must keep working next to a newer citry 1.x. So
each name, parameter, class member and constant value recorded in
``lsp_support_names.json`` must stay usable the same way. Additions are
fine: a new name, a new optional parameter, a new class member.

Recording a new name: run this file as a script
(``python packages/py/citry/tests/test_lsp_support_module.py``). It adds
the names, parameters and members that the JSON file does not list yet,
and keeps every recorded entry that the current code would break.

Until the ``citry@1.0.0`` tag exists, these internals may still change,
so delete the JSON file and run the script to record it again. The 1.0.0
release pull request does that one last time. After 1.0.0, editing a
recorded entry by hand is a breaking change for citry-lsp and waits for
citry 2.0.0.

The checks cannot see return types or the arguments a function passes to
a callback; the release check in ``scripts/lsp_citry_pairs.py``, which
runs citry-lsp's tests, covers those.
"""

from __future__ import annotations

import enum
import functools
import inspect
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

import pytest

from citry import _lsp_support

if TYPE_CHECKING:
    from citry import Citry

SNAPSHOT = Path(__file__).with_name("lsp_support_names.json")

# Plain values whose exact value citry-lsp relies on, such as diagnostic
# codes. A collection is recorded by its type and, when it holds strings,
# its entries (a dict's keys): adding an entry (a new HTML element, a new
# lint rule) is an allowed addition, removing one is not.
_EXACT_VALUE_TYPES = (str, int, float, bool)
_COLLECTION_TYPES = (dict, list, tuple, set, frozenset)
# `*args` and `**kwargs` are matched by kind, so renaming one is harmless.
_VARIADIC = ("VAR_POSITIONAL", "VAR_KEYWORD")


def _default_text(value: object) -> str:
    """Return a default value as text that stays the same from one run to the next."""
    # A set prints in hash order, which changes between runs for strings.
    if isinstance(value, (set, frozenset)):
        return f"{type(value).__name__}({', '.join(sorted(map(repr, value)))})"
    text = repr(value)
    # A sentinel object's repr carries its memory address, which changes on
    # every run, so the type name stands in for it.
    if " at 0x" in text:
        return f"<{type(value).__qualname__}>"
    return text


def _signature_record(target: Any) -> list[dict[str, str]] | None:
    """Describe each parameter by name, kind and default, or return None when Python cannot read it."""
    try:
        signature = inspect.signature(target)
    except (TypeError, ValueError):
        return None
    record = []
    for parameter in signature.parameters.values():
        item = {"name": parameter.name, "kind": parameter.kind.name}
        if parameter.default is not inspect.Parameter.empty:
            item["default"] = _default_text(parameter.default)
        record.append(item)
    # Annotations are left out: a widened type is not a break, and the
    # release check runs citry-lsp's tests, which use the real types.
    return record


def _builtin_names(cls: type) -> set[str]:
    """Names a class gets from a built-in base such as ``object`` or ``ValueError``."""
    names: set[str] = set()
    for base in cls.__mro__:
        if base.__module__ == "builtins":
            names.update(dir(base))
    return names


def _member_record(cls: type, name: str) -> dict[str, Any]:
    """Describe one public class member the way citry-lsp can use it."""
    raw = inspect.getattr_static(cls, name)
    if isinstance(raw, (staticmethod, classmethod)) or inspect.isfunction(raw):
        return {"kind": "method", "signature": _signature_record(getattr(cls, name))}
    # A property, a cached property and a plain attribute are all read as
    # `obj.name`, so switching between them is not a break.
    if isinstance(raw, (property, functools.cached_property)):
        return {"kind": "attribute"}
    value = getattr(cls, name)
    if isinstance(value, _EXACT_VALUE_TYPES):
        return {"kind": "value", "value": value}
    return {"kind": "attribute"}


def _class_record(cls: type) -> dict[str, Any]:
    """Describe a class by its public members, its fields and how it is constructed."""
    if issubclass(cls, enum.Enum):
        return {"kind": "enum", "members": {member.name: {"kind": "value", "value": member.value} for member in cls}}
    skip = _builtin_names(cls)
    members = {name: _member_record(cls, name) for name in dir(cls) if not name.startswith("_") and name not in skip}
    # An annotated instance attribute without a class-level value, such as
    # a dataclass field without a default or `PythonTemplateFormatError.range`,
    # is missing from `dir()`, and citry-lsp reads it on every instance.
    for base in cls.__mro__:
        if base.__module__ == "builtins":
            continue
        for name in inspect.get_annotations(base):
            if not name.startswith("_"):
                members.setdefault(name, {"kind": "attribute"})
    return {"kind": "class", "init": _signature_record(cls), "members": dict(sorted(members.items()))}


def _record(value: object) -> dict[str, Any]:
    """Describe one exported name."""
    if inspect.isclass(value):
        return _class_record(value)
    if callable(value):
        return {"kind": "function", "signature": _signature_record(value)}
    if isinstance(value, _EXACT_VALUE_TYPES):
        return {"kind": "value", "value": value}
    if isinstance(value, _COLLECTION_TYPES):
        record: dict[str, Any] = {"kind": "collection", "type": type(value).__name__}
        entries = list(value)
        if all(isinstance(entry, str) for entry in entries):
            record["entries"] = sorted(entries)
        return record
    # Such as `symtable`, which is a module, or None on PyPy.
    return {"kind": "object"}


def current_records() -> dict[str, dict[str, Any]]:
    """Describe every name the module exports today."""
    return {name: _record(getattr(_lsp_support, name)) for name in sorted(_lsp_support.__all__)}


def _signature_problems(where: str, old: list[dict[str, str]] | None, new: list[dict[str, str]] | None) -> list[str]:
    """List the ways a call that worked with the old signature can fail with the new one."""
    if old is None or new is None:
        return [] if old == new else [f"{where}: Python can no longer read its signature"]
    problems = []
    new_by_name = {parameter["name"]: parameter for parameter in new}
    old_names = {parameter["name"] for parameter in old}
    positional = ("POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD")
    for index, parameter in enumerate(old):
        name = parameter["name"]
        if parameter["kind"] in _VARIADIC:
            place = next((at for at, item in enumerate(new) if item["kind"] == parameter["kind"]), None)
            if place is None:
                problems.append(f"{where}: parameter {name!r} was removed")
            # A new parameter before `*args` would take a value meant for it.
            elif parameter["kind"] == "VAR_POSITIONAL" and place != index:
                problems.append(f"{where}: positional parameter {name!r} moved")
            continue
        current = new_by_name.get(name)
        if current is None:
            problems.append(f"{where}: parameter {name!r} was removed")
            continue
        # A positional argument is matched by place, so it must keep its place.
        if parameter["kind"] in positional and (index >= len(new) or new[index]["name"] != name):
            problems.append(f"{where}: positional parameter {name!r} moved")
        # A keyword-only parameter may become positional-or-keyword, which
        # still accepts the keyword; every other change of kind breaks a call.
        widened = parameter["kind"] == "KEYWORD_ONLY" and current["kind"] == "POSITIONAL_OR_KEYWORD"
        if current["kind"] != parameter["kind"] and not widened:
            problems.append(f"{where}: parameter {name!r} changed from {parameter['kind']} to {current['kind']}")
        if "default" in parameter and current.get("default") != parameter["default"]:
            problems.append(f"{where}: default of {name!r} changed from {parameter['default']}")
    for parameter in new:
        variadic = parameter["kind"] in _VARIADIC
        if parameter["name"] not in old_names and "default" not in parameter and not variadic:
            problems.append(f"{where}: new parameter {parameter['name']!r} has no default")
    return problems


def compatibility_problems(old: dict[str, Any], new: dict[str, Any], where: str) -> list[str]:
    """List every way ``new`` breaks code written against ``old``."""
    if old["kind"] != new["kind"]:
        return [f"{where}: changed from {old['kind']} to {new['kind']}"]
    problems: list[str] = []
    if "value" in old and old["value"] != new.get("value"):
        problems.append(f"{where}: value changed from {old['value']!r} to {new.get('value')!r}")
    if old.get("type") != new.get("type"):
        problems.append(f"{where}: type changed from {old.get('type')} to {new.get('type')}")
    missing = sorted(set(old.get("entries", ())) - set(new.get("entries", ())))
    if missing:
        problems.append(f"{where}: entries removed: {missing}")
    for key in ("signature", "init"):
        if key in old:
            label = where if key == "signature" else f"{where}()"
            problems += _signature_problems(label, old[key], new.get(key))
    for name, member in old.get("members", {}).items():
        current = new.get("members", {}).get(name)
        if current is None:
            problems.append(f"{where}.{name}: removed")
        else:
            problems += compatibility_problems(member, current, f"{where}.{name}")
    return problems


def _merged(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Record what is new, and keep each recorded entry that the current code would break."""
    merged = dict(old)
    for name, record in new.items():
        # A compatible record only adds to the old one (a new parameter, a
        # new member), so it replaces it; a breaking one stays out, so the
        # test keeps failing until the code is fixed.
        if name not in merged or not compatibility_problems(merged[name], record, name):
            merged[name] = record
    return dict(sorted(merged.items()))


def test_every_recorded_name_still_works_the_same_way() -> None:
    recorded = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    current = current_records()
    problems = []
    for name, record in recorded.items():
        if name not in current:
            problems.append(f"{name}: removed from citry._lsp_support")
        else:
            problems += compatibility_problems(record, current[name], name)
    assert not problems, "citry-lsp 1.x relies on these:\n" + "\n".join(problems)


def test_every_exported_name_is_recorded() -> None:
    # An unrecorded name would get no protection, so a new name is
    # recorded in the same change that adds it.
    recorded = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    missing = sorted(set(_lsp_support.__all__) - set(recorded))
    assert not missing, f"record these by running {Path(__file__).name} as a script: {missing}"


def test_every_exported_name_exists() -> None:
    assert sorted(_lsp_support.__all__) == sorted(set(_lsp_support.__all__))
    assert [name for name in _lsp_support.__all__ if not hasattr(_lsp_support, name)] == []


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        pytest.param(
            [{"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}],
            [{"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}, {"name": "b", "kind": "KEYWORD_ONLY", "default": "1"}],
            [],
            id="optional-parameter-added",
        ),
        pytest.param(
            [{"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}],
            [{"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}, {"name": "b", "kind": "KEYWORD_ONLY"}],
            ["f: new parameter 'b' has no default"],
            id="required-parameter-added",
        ),
        pytest.param(
            [{"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}, {"name": "b", "kind": "POSITIONAL_OR_KEYWORD"}],
            [{"name": "b", "kind": "POSITIONAL_OR_KEYWORD"}, {"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}],
            ["f: positional parameter 'a' moved", "f: positional parameter 'b' moved"],
            id="reordered",
        ),
        pytest.param(
            [{"name": "a", "kind": "KEYWORD_ONLY", "default": "None"}],
            [{"name": "a", "kind": "KEYWORD_ONLY", "default": "1"}],
            ["f: default of 'a' changed from None"],
            id="default-changed",
        ),
        pytest.param(
            [{"name": "a", "kind": "KEYWORD_ONLY"}],
            [{"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}],
            [],
            id="keyword-only-widened",
        ),
        pytest.param(
            [{"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}],
            [],
            ["f: parameter 'a' was removed"],
            id="removed",
        ),
    ],
)
def test_signature_check_accepts_additions_and_rejects_breaks(
    old: list[dict[str, str]], new: list[dict[str, str]], expected: list[str]
) -> None:
    assert _signature_problems("f", old, new) == expected


def test_member_and_value_checks_reject_breaks() -> None:
    old = {
        "kind": "class",
        "init": [],
        "members": {"x": {"kind": "attribute"}, "CODE": {"kind": "value", "value": "a"}},
    }
    added = {
        "kind": "class",
        "init": [],
        "members": {"x": {"kind": "attribute"}, "CODE": {"kind": "value", "value": "a"}, "y": {"kind": "property"}},
    }
    broken = {"kind": "class", "init": [], "members": {"CODE": {"kind": "value", "value": "b"}}}

    assert compatibility_problems(old, added, "C") == []
    assert compatibility_problems(old, broken, "C") == ["C.x: removed", "C.CODE: value changed from 'a' to 'b'"]


def test_variadic_parameters_are_matched_by_kind_and_place() -> None:
    old = [{"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}, {"name": "args", "kind": "VAR_POSITIONAL"}]
    inserted = [
        {"name": "a", "kind": "POSITIONAL_OR_KEYWORD"},
        {"name": "extra", "kind": "POSITIONAL_OR_KEYWORD", "default": "None"},
        {"name": "args", "kind": "VAR_POSITIONAL"},
    ]
    renamed = [{"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}, {"name": "rest", "kind": "VAR_POSITIONAL"}]

    assert _signature_problems("f", old, inserted) == ["f: positional parameter 'args' moved"]
    assert _signature_problems("f", old, renamed) == []
    assert _signature_problems("f", old, old[:1]) == ["f: parameter 'args' was removed"]


def test_a_collection_may_gain_entries_but_not_lose_them() -> None:
    old = {"kind": "collection", "type": "frozenset", "entries": ["a", "b"]}

    assert compatibility_problems(old, {**old, "entries": ["a", "b", "c"]}, "S") == []
    assert compatibility_problems(old, {**old, "entries": ["a"]}, "S") == ["S: entries removed: ['b']"]


def test_recording_adds_to_compatible_entries_and_keeps_breaking_ones() -> None:
    old = {"f": {"kind": "function", "signature": [{"name": "a", "kind": "POSITIONAL_OR_KEYWORD"}]}}
    added = {
        "f": {
            "kind": "function",
            "signature": [
                {"name": "a", "kind": "POSITIONAL_OR_KEYWORD"},
                {"name": "b", "kind": "KEYWORD_ONLY", "default": "None"},
            ],
        }
    }
    broken = {"f": {"kind": "function", "signature": []}}

    assert _merged(old, added) == added
    assert _merged(old, broken) == old


def test_an_annotated_instance_attribute_is_recorded() -> None:
    class Failure(ValueError):
        code: str

        def __init__(self, code: str) -> None:
            super().__init__(code)
            self.code = code

    assert _record(Failure)["members"] == {"code": {"kind": "attribute"}}


class _Extensions:
    def __init__(self, extension: object | None) -> None:
        self._extension = extension

    def get_extension(self, name: str) -> object:
        if self._extension is None:
            msg = f"Extension {name!r} not found"
            raise ValueError(msg)
        return self._extension


@pytest.mark.parametrize(
    ("extension", "expected"),
    [
        pytest.param(None, None, id="no-i18n-extension"),
        pytest.param(SimpleNamespace(), None, id="replaced-extension-without-an-index"),
        pytest.param(SimpleNamespace(_tooling_index=lambda: {"version": 1}), {"version": 1}, id="index"),
    ],
)
def test_i18n_tooling_index(extension: object | None, expected: dict[str, object] | None) -> None:
    engine = cast("Citry", SimpleNamespace(extensions=_Extensions(extension)))

    assert _lsp_support.i18n_tooling_index(engine) == expected


def _snapshot_text(records: dict[str, Any]) -> str:
    """Write the records as JSON with one parameter or member per line, so a diff shows each change."""
    text = json.dumps(records, indent=1)
    # Fold each innermost object (a parameter or a simple member) onto one line.
    return (
        re.sub(r"\{\n\s*([^{}\[\]]*?)\n\s*\}", lambda match: "{" + re.sub(r"\n\s*", " ", match[1]) + "}", text) + "\n"
    )


if __name__ == "__main__":
    existing = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {}
    SNAPSHOT.write_text(_snapshot_text(_merged(existing, current_records())), encoding="utf-8")
    sys.stdout.write(f"wrote {SNAPSHOT}\n")
