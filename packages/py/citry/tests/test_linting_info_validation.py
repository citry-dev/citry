"""
Check that the lint records the app worker sends the language server reject malformed values.

The records must also survive a round trip through a dict.
"""

from __future__ import annotations

import re

import pytest

from citry import Citry
from citry._linting import (
    TemplateLintInfo,
    TemplateVariableInfo,
    VueVariableInfo,
)


def _lint_info(**changes: object) -> TemplateLintInfo:
    fields: dict[str, object] = {"rule_unknown_template_variable": "warning", "template_variables": ()}
    fields.update(changes)
    return TemplateLintInfo(**fields)  # type: ignore[arg-type]


def _template_var(**changes: object) -> TemplateVariableInfo:
    fields: dict[str, object] = {
        "name": "title",
        "type_display": "str",
        "type_fidelity": "normalized",
        "description": None,
        "source": "component",
    }
    fields.update(changes)
    return TemplateVariableInfo(**fields)  # type: ignore[arg-type]


def _vue_var(**changes: object) -> VueVariableInfo:
    fields: dict[str, object] = {
        "name": "count",
        "type_display": "int",
        "type_fidelity": "normalized",
        "description": None,
        "source": "component",
    }
    fields.update(changes)
    return VueVariableInfo(**fields)  # type: ignore[arg-type]


_BAD_VARIABLE_FIELDS = [
    pytest.param({"type_display": None}, "type fidelity must match", id="no-display-but-normalized"),
    pytest.param({"type_fidelity": "unavailable"}, "type fidelity must match", id="display-but-unavailable"),
    pytest.param({"type_display": "\ud800"}, "valid UTF-8", id="type-display-lone-surrogate"),
    pytest.param({"type_display": "List[str]  "}, "canonical passive annotation", id="type-display-not-canonical"),
    pytest.param({"description": ""}, "non-empty strings or None", id="empty-description"),
    pytest.param({"description": "\ud800"}, "valid UTF-8", id="description-lone-surrogate"),
    pytest.param({"source": "nowhere"}, "Unknown .* variable source", id="unknown-source"),
]


@pytest.mark.parametrize(("changes", "message"), _BAD_VARIABLE_FIELDS)
def test_template_variable_info_rejects_malformed_fields(changes, message):
    with pytest.raises(ValueError, match=message):
        _template_var(**changes)


@pytest.mark.parametrize(("changes", "message"), _BAD_VARIABLE_FIELDS)
def test_vue_variable_info_rejects_malformed_fields(changes, message):
    with pytest.raises(ValueError, match=message):
        _vue_var(**changes)


def test_variable_info_rejects_an_invalid_variable_name():
    with pytest.raises(ValueError, match="Invalid portable template variable name"):
        _template_var(name="not a name")
    with pytest.raises(ValueError, match="Invalid portable Vue variable name"):
        _vue_var(name="1bad")


def test_variable_info_round_trips_through_a_dict():
    template = _template_var(description="The page title.")
    vue = _vue_var(type_display=None, type_fidelity="unavailable")
    assert TemplateVariableInfo.from_dict(template.to_dict()) == template
    assert VueVariableInfo.from_dict(vue.to_dict()) == vue


@pytest.mark.parametrize("cls", [TemplateVariableInfo, VueVariableInfo], ids=["template", "vue"])
def test_variable_info_from_dict_requires_the_exact_fields(cls):
    record = _template_var().to_dict()
    with pytest.raises(ValueError, match="exact supported fields"):
        cls.from_dict({**record, "extra": 1})
    with pytest.raises(ValueError, match="exact supported fields"):
        cls.from_dict({k: v for k, v in record.items() if k != "source"})
    with pytest.raises(ValueError, match="exact supported fields"):
        cls.from_dict([record])


_BAD_SEVERITY_FIELDS = [
    ("rule_unknown_template_variable", "Unknown template lint severity"),
    ("rule_i18n_missing_param_type", "Unknown i18n missing-param lint severity"),
    ("rule_unknown_vue_variable", "Unknown Vue lint severity"),
    ("rule_unknown_component_js_variable", "Unknown component-JavaScript lint severity"),
    ("rule_unknown_component_js_member", "Unknown component-JavaScript member lint severity"),
    ("rule_vue_python_variable", "Unknown Vue Python-variable lint severity"),
    ("rule_alpine_attribute", "Unknown Alpine-attribute lint severity"),
    ("rule_alpine_cloak", "Unknown Alpine x-cloak lint severity"),
    ("rule_invalid_attribute_value", "Unknown attribute-value lint severity"),
    ("rule_misspelled_directive", "Unknown misspelled-directive lint severity"),
    ("rule_i18n_cross_language_fallback", "Unknown i18n cross-language fallback lint severity"),
]


@pytest.mark.parametrize(
    ("field_name", "message"),
    [pytest.param(name, message, id=name) for name, message in _BAD_SEVERITY_FIELDS],
)
def test_template_lint_info_rejects_an_unknown_severity(field_name, message):
    with pytest.raises(ValueError, match=message):
        _lint_info(**{field_name: "fatal"})


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        pytest.param(
            {"template_variables": [_template_var()]}, "template_variables must be a tuple", id="template-list"
        ),
        pytest.param({"vue_variables": [_vue_var()]}, "vue_variables must be a tuple", id="vue-list"),
        pytest.param(
            {"component_js_globals": [_vue_var()]}, "component_js_globals must be a tuple", id="js-globals-list"
        ),
        pytest.param({"allows_extra_variables": 1}, "allows_extra_variables must be a bool", id="extra-variables-int"),
    ],
)
def test_template_lint_info_rejects_values_of_the_wrong_type(changes, message):
    with pytest.raises(TypeError, match=message):
        _lint_info(**changes)


def test_template_lint_info_requires_variables_sorted_and_unique():
    first, second = _template_var(name="a"), _template_var(name="b")
    with pytest.raises(ValueError, match="Template lint variables must be unique and sorted"):
        TemplateLintInfo("warning", (second, first))
    with pytest.raises(ValueError, match="Template lint variables must be unique and sorted"):
        TemplateLintInfo("warning", (first, first))
    vue_a, vue_b = _vue_var(name="a"), _vue_var(name="b")
    with pytest.raises(ValueError, match="Vue lint variables must be unique and sorted"):
        TemplateLintInfo("warning", (), vue_variables=(vue_b, vue_a))
    with pytest.raises(ValueError, match="Component JavaScript globals must be unique and sorted"):
        TemplateLintInfo("warning", (), component_js_globals=(vue_b, vue_a))


@pytest.mark.parametrize(
    "keys",
    [
        pytest.param(["a"], id="list-not-tuple"),
        pytest.param(("b", "a"), id="unsorted"),
        pytest.param(("a", "a"), id="duplicate"),
        pytest.param(("not a name",), id="invalid-name"),
        pytest.param((1,), id="non-string"),
    ],
)
def test_template_lint_info_rejects_malformed_template_data_keys(keys):
    with pytest.raises(ValueError, match=re.escape("template_data_keys must be None or a sorted tuple")):
        TemplateLintInfo("warning", (), template_data_keys=keys)  # type: ignore[arg-type]


def test_template_lint_info_dict_carries_template_data_keys_only_when_set():
    # Round trips and the null case are covered in test_lint_template_data_keys.py;
    # this checks only that an unset list is left out of the dict.
    assert "template_data_keys" not in TemplateLintInfo("warning", ()).to_dict()


def test_template_lint_info_from_dict_rejects_malformed_records():
    record = TemplateLintInfo("warning", ()).to_dict()
    with pytest.raises(ValueError, match="exact supported fields"):
        TemplateLintInfo.from_dict({**record, "surprise": 1})
    with pytest.raises(ValueError, match="exact supported fields"):
        TemplateLintInfo.from_dict("nope")
    for field_name in ("template_variables", "vue_variables", "component_js_globals"):
        with pytest.raises(ValueError, match=f"{field_name} must be a list"):
            TemplateLintInfo.from_dict({**record, field_name: ()})
    with pytest.raises(ValueError, match="template_data_keys must be null or a list"):
        TemplateLintInfo.from_dict({**record, "template_data_keys": "a"})


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, None, id="none"),
        pytest.param(3, "int", id="scalar"),
        pytest.param([1, 2], "list[int]", id="list-of-one-type"),
        pytest.param({"a": 1}, "dict[str, int]", id="dict-of-one-type"),
        pytest.param([1, "a"], None, id="mixed-list"),
        pytest.param([], None, id="empty-list"),
        pytest.param({}, None, id="empty-dict"),
        pytest.param({"a": 1, 2: 3}, None, id="mixed-dict-keys"),
        pytest.param({"a": 1, "b": "x"}, None, id="mixed-dict-values"),
    ],
)
def test_runtime_type_display_names_a_type_only_when_every_element_agrees(value, expected):
    engine = Citry(autodiscover=False, template_globals={"probe": value})
    by_name = {item.name: item for item in engine.template_analysis().lint.template_variables}
    assert by_name["probe"].type_display == expected


def test_runtime_type_display_gives_no_type_for_a_dict_that_holds_itself():
    # A dict that contains itself cannot be described, and must not recurse forever.
    looped: dict[str, object] = {}
    looped["me"] = looped
    engine = Citry(autodiscover=False, template_globals={"probe": looped})
    by_name = {item.name: item for item in engine.template_analysis().lint.template_variables}
    assert by_name["probe"].type_display is None
