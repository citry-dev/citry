from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import fields

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import (
    CField,
    CForm,
    CNativeSelect,
    CNativeSelectGroup,
    CNativeSelectOption,
)


def _render(value: object) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "<main>{{ value }}</main>"

        def template_data(self, kwargs, slots):
            return {"value": value}

    return Page().render().serialize(deps_strategy="ignore")


def _root(html: str) -> str:
    match = re.search(r'<select[^>]+data-citry-ui-part="native-select"[^>]*>', html)
    assert match is not None
    return match.group(0)


def test_native_select_schema_and_public_records_are_exact():
    assert [field.name for field in fields(CNativeSelect.Kwargs)] == [
        "options",
        "name",
        "id",
        "value",
        "placeholder",
        "required",
        "disabled",
        "invalid",
        "autocomplete",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert fields(CNativeSelect.Slots) == ()
    assert [field.name for field in fields(CNativeSelectOption)] == ["value", "label", "disabled", "attrs"]
    assert [field.name for field in fields(CNativeSelectGroup)] == ["label", "options", "disabled", "attrs"]


def test_native_select_renders_one_native_root_with_ordered_options_and_groups():
    html = _render(
        CNativeSelect(
            name="habitat",
            options=[
                CNativeSelectOption("reef", "Coral reef"),
                CNativeSelectGroup(
                    "Open ocean",
                    [CNativeSelectOption("pelagic", "Pelagic"), CNativeSelectOption("abyss", "Abyss")],
                ),
            ],
            placeholder="Choose a habitat",
            required=True,
        )
    )
    root = _root(html)

    assert html.count("<select") == 1
    assert root.count("<select") == 1
    assert 'name="habitat"' in root
    assert " required" in root
    assert html.index("Choose a habitat") < html.index("Coral reef") < html.index("Open ocean") < html.index("Pelagic")
    assert '<optgroup label="Open ocean">' in html
    assert 'data-citry-key=":native-select-option-' in html


@pytest.mark.parametrize("value", [None, ""])
def test_placeholder_is_the_only_empty_option_and_is_selected_for_empty_server_value(value):
    html = _render(
        CNativeSelect(
            options=[CNativeSelectOption("reef", "Reef")],
            placeholder="Choose",
            value=value,
        )
    )

    assert re.search(r"<option value selected[^>]*>Choose</option>", html) is not None
    assert html.count("<option value ") == 1
    assert " data-empty" in _root(html)


def test_selected_value_marks_exact_enabled_option_and_root_customization_merges():
    html = _render(
        CNativeSelect(
            options=[CNativeSelectOption("reef", "Reef"), CNativeSelectOption("kelp", "Kelp")],
            value="kelp",
            class_="survey-control",
            style={"--cui-native-select-radius": "1rem"},
            attrs={"class": "from-attrs", "data-survey": "ocean"},
        )
    )
    root = _root(html)

    assert re.search(r'<option value="kelp" selected[^>]*>Kelp</option>', html) is not None
    assert "survey-control" in root
    assert "from-attrs" in root
    assert "--cui-native-select-radius: 1rem" in root
    assert 'data-survey="ocean"' in root
    assert " data-empty" not in root


@pytest.mark.parametrize(
    ("component", "message"),
    [
        (CNativeSelect(options=[], required=True), "requires placeholder"),
        (CNativeSelect(options=[], value=""), "requires placeholder"),
        (
            CNativeSelect(
                options=[CNativeSelectOption("reef", "Reef", disabled=True)],
                value="reef",
            ),
            "disabled option",
        ),
        (
            CNativeSelect(
                options=[CNativeSelectGroup("Sea", [CNativeSelectOption("reef", "Reef")], disabled=True)],
                value="reef",
            ),
            "disabled option",
        ),
    ],
)
def test_native_select_rejects_nonconforming_required_and_selected_values(component, message):
    with pytest.raises(ValueError, match=message):
        _render(component)


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ("reef", "must be a sequence"),
        ([object()], "option or group records"),
        ([CNativeSelectOption("", "Empty")], "non-empty string"),
        ([CNativeSelectOption("reef", "")], "non-empty string"),
        ([CNativeSelectOption("reef", "Reef", disabled=1)], "must be a bool"),
        ([CNativeSelectGroup("Sea", "reef")], "group options must be a sequence"),
        (
            [CNativeSelectOption("a\rb", "One"), CNativeSelectOption("a\nb", "Two")],
            "unique after normalization",
        ),
        ([CNativeSelectOption("a\0b", "Nul")], r"U\+0000"),
    ],
)
def test_native_select_rejects_invalid_option_collections(options, message):
    with pytest.raises((TypeError, ValueError), match=message):
        _render(CNativeSelect(options=options))


def test_server_value_and_option_value_share_newline_canonicalization():
    html = _render(
        CNativeSelect(
            options=[CNativeSelectOption("north\r\nsouth", "North to south")],
            value="north\rsouth",
        )
    )

    assert 'value="north\nsouth" selected' in html


def test_direct_text_inputs_are_de_trusted_and_non_string_html_protocol_is_rejected():
    html = _render(
        CNativeSelect(
            options=[CNativeSelectOption("reef", Markup("<b>Reef</b>"))],
            placeholder=Markup("<Choose>"),
        )
    )

    assert "<b>Reef</b>" not in html
    assert "&lt;b&gt;Reef&lt;/b&gt;" in html
    assert "&lt;Choose&gt;" in html

    class Trusted:
        def __html__(self):
            return "reef"

    with pytest.raises(TypeError, match="must be a string"):
        _render(CNativeSelect(options=[CNativeSelectOption(Trusted(), "Reef")]))


@pytest.mark.parametrize(
    ("attrs", "message"),
    [
        ({"readonly": True}, "owned attribute"),
        ({":multiple": "many"}, "dynamically bind owned"),
        ({"X-BIND:VALUE": "chosen"}, "dynamically bind owned"),
        ({".required": True}, "dynamically bind owned"),
        ({":form": "owner"}, "dynamically bind owned"),
        ({"X-BIND:FORM": "owner"}, "dynamically bind owned"),
        ({".form": "owner"}, "dynamically bind owned"),
        ({"x-bind": {"value": "reef"}}, "ownership directive"),
        ({"x-model": "reef"}, "ownership directive"),
        ({"x-html": "options"}, "ownership directive"),
        ({"data-citry-root": "x"}, "reserved Citry runtime"),
    ],
)
def test_root_attrs_reject_second_ownership_paths(attrs, message):
    with pytest.raises(ValueError, match=message):
        _render(CNativeSelect(options=[], attrs=attrs))


def test_native_event_and_unrelated_alpine_attrs_remain_allowed():
    root = _root(
        _render(
            CNativeSelect(
                options=[CNativeSelectOption("reef", "Reef")],
                attrs={"@change": "changed = true", ":title": "hint"},
            )
        )
    )

    assert '@change="changed = true"' in root
    assert ':title="hint"' in root


def test_option_and_group_attrs_are_copied_validated_and_rendered():
    option_attrs = {"class": "reef-option", "data-depth": "shallow"}
    group_attrs = {"data-region": "pacific"}
    option = CNativeSelectOption("reef", "Reef", attrs=option_attrs)
    group = CNativeSelectGroup("Pacific", [option], attrs=group_attrs)
    value = CNativeSelect(options=[group])
    option_attrs["selected"] = True
    group_attrs["label"] = "Changed"

    with pytest.raises(ValueError, match="owned attribute"):
        _render(value)


class _OneShotSequence(Sequence[object]):
    def __init__(self, values: list[object]) -> None:
        self.values = values
        self.iterations = 0

    def __len__(self) -> int:
        return len(self.values)

    def __getitem__(self, index: int) -> object:
        return self.values[index]

    def __iter__(self) -> Iterator[object]:
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("sequence was read more than once")
        return iter(self.values)


class _OneShotMapping(Mapping[str, object]):
    def __init__(self) -> None:
        self.iterations = 0

    def __iter__(self) -> Iterator[str]:
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("mapping was read more than once")
        return iter(("data-probe",))

    def __len__(self) -> int:
        return 1

    def __getitem__(self, key: str) -> object:
        if key != "data-probe":
            raise KeyError(key)
        return "snapshot"


def test_nested_sequences_and_mappings_are_snapshotted_once_per_render():
    options = _OneShotSequence([CNativeSelectOption("reef", "Reef", attrs=_OneShotMapping())])
    html = _render(CNativeSelect(options=options))

    assert options.iterations == 1
    assert 'data-probe="snapshot"' in html


def test_field_required_capability_and_readonly_errors_are_server_coherent():
    valid = _render(
        CField(
            required=True,
            slots={
                "label": "Habitat",
                "default": CNativeSelect(
                    options=[CNativeSelectOption("reef", "Reef")],
                    placeholder="Choose",
                ),
            },
        )
    )
    root = _root(valid)
    assert " required" in root
    assert 'data-citry-field-supports-required="true"' in root
    assert 'data-citry-field-supports-readonly="false"' in root

    with pytest.raises(ValueError, match="required=True is not supported"):
        _render(
            CField(
                required=True,
                slots={"label": "Habitat", "default": CNativeSelect(options=[])},
            )
        )
    with pytest.raises(ValueError, match="readonly=True is not supported"):
        _render(
            CField(
                readonly=True,
                slots={
                    "label": "Habitat",
                    "default": CNativeSelect(options=[], placeholder="Choose"),
                },
            )
        )


def test_readonly_form_requires_explicit_field_opt_out_but_standalone_select_ignores_it():
    with pytest.raises(ValueError, match="readonly=True is not supported"):
        _render(
            CForm(
                readonly=True,
                slots={
                    "default": CField(
                        slots={
                            "label": "Habitat",
                            "default": CNativeSelect(options=[], placeholder="Choose"),
                        }
                    )
                },
            )
        )

    field_html = _render(
        CForm(
            readonly=True,
            slots={
                "default": CField(
                    readonly=False,
                    slots={
                        "label": "Habitat",
                        "default": CNativeSelect(options=[], placeholder="Choose"),
                    },
                )
            },
        )
    )
    standalone_html = _render(
        CForm(
            readonly=True,
            slots={"default": CNativeSelect(options=[], placeholder="Choose")},
        )
    )
    assert field_html.count('data-citry-ui-part="native-select"') == 1
    assert standalone_html.count('data-citry-ui-part="native-select"') == 1


def test_field_relationships_merge_external_idrefs_without_duplicates():
    root = _root(
        _render(
            CField(
                control_id="habitat",
                invalid=True,
                slots={
                    "label": "Habitat",
                    "description": "Choose one",
                    "error": "Selection required",
                    "default": CNativeSelect(
                        options=[],
                        placeholder="Choose",
                        attrs={
                            "ARIA-DESCRIBEDBY": "external habitat-description",
                            "ARIA-ERRORMESSAGE": "external-error",
                        },
                    ),
                },
            )
        )
    )

    assert 'aria-describedby="habitat-description habitat-error external"' in root
    assert 'aria-errormessage="habitat-error external-error"' in root


def test_html_attribute_lookup_rejects_case_insensitive_form_conflicts_and_duplicates():
    with pytest.raises(ValueError, match="different native form owner"):
        _render(
            CForm(
                id="inside",
                slots={
                    "default": CNativeSelect(
                        options=[],
                        placeholder="Choose",
                        attrs={"FORM": "outside"},
                    )
                },
            )
        )

    with pytest.raises(ValueError, match="duplicate case variants"):
        _render(
            CNativeSelect(
                options=[],
                placeholder="Choose",
                attrs={"aria-describedby": "first", "ARIA-DESCRIBEDBY": "second"},
            )
        )


@pytest.mark.parametrize("omitted_value", [None, False])
def test_omitted_case_insensitive_form_attr_keeps_the_enclosing_owner(omitted_value):
    root = _root(
        _render(
            CForm(
                id="inside",
                slots={
                    "default": CNativeSelect(
                        options=[],
                        placeholder="Choose",
                        attrs={"FORM": omitted_value},
                    )
                },
            )
        )
    )

    assert " form=" not in root.lower()


def test_native_select_assets_exports_and_no_slot_contract():
    app = Citry(autodiscover=False)
    installation = app.register_library(citry_ui)
    concrete = installation[CNativeSelect]

    assert citry_ui.CNativeSelect is CNativeSelect
    assert concrete.get_js()
    assert concrete.get_css()
    assert "MutationObserver" not in concrete.get_js()
    assert "setInterval" not in concrete.get_js()
    with pytest.raises(TypeError, match="unexpected keyword argument 'default'"):
        _render(CNativeSelect(options=[], slots={"default": "No"}))
