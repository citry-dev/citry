from __future__ import annotations

import re
from dataclasses import fields

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CContainer, CGrid, CGridItem
from citry_ui.quality.asset_sources import read_component_source_css


def _render(layout: object, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>{{ layout }}</main>{{ css }}
        """

        def template_data(self, kwargs, slots):
            return {
                "layout": layout,
                "css": app.get("css")() if include_css else "",
            }

    return str(Page())


def _render_static_template() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <c-CContainer size="lg" gutter="xl">
            <c-CGrid cols="12" sm="2" md="3" lg="4" xl="5" xxl="6">
              <c-CGridItem tag="article" span="12" sm="6" md="4" lg="3" xl="2" xxl="1">
                Feldspar
              </c-CGridItem>
            </c-CGrid>
          </c-CContainer>
        """

    return str(Page())


def test_schemas_keep_the_responsive_surface_flat():
    assert [field.name for field in fields(CContainer.Kwargs)] == [
        "tag",
        "size",
        "fluid",
        "gutter",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CGrid.Kwargs)] == [
        "tag",
        "cols",
        "sm",
        "md",
        "lg",
        "xl",
        "xxl",
        "min_col",
        "gap",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CGridItem.Kwargs)] == [
        "tag",
        "span",
        "sm",
        "md",
        "lg",
        "xl",
        "xxl",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CContainer.Slots)] == ["default"]
    assert [field.name for field in fields(CGrid.Slots)] == ["default"]
    assert [field.name for field in fields(CGridItem.Slots)] == ["default"]


def test_defaults_render_one_root_each_without_admin_wrappers():
    item = CGridItem(slots={"default": "Quartz"})
    grid = CGrid(slots={"default": item})
    html = _render(CContainer(slots={"default": grid}))

    container_roots = re.findall(r'<[^>]+data-citry-ui-part="container"[^>]*>', html)
    grid_roots = re.findall(r'<[^>]+data-citry-ui-part="grid"[^>]*>', html)
    item_roots = re.findall(r'<[^>]+data-citry-ui-part="grid-item"[^>]*>', html)
    assert len(container_roots) == 1
    assert len(grid_roots) == 1
    assert len(item_roots) == 1
    assert 'data-size="xl"' in container_roots[0]
    assert 'data-gutter="lg"' in container_roots[0]
    assert 'data-cols="1"' in grid_roots[0]
    assert 'data-gap="md"' in grid_roots[0]
    assert 'data-span="1"' in item_roots[0]
    assert "data-fluid" not in container_roots[0]
    assert "data-intrinsic" not in grid_roots[0]
    assert "cui-grid__" not in html


def test_static_template_decimal_inputs_stay_concise():
    html = _render_static_template()

    assert 'data-cols="12"' in html
    assert 'data-cols-sm="2"' in html
    assert 'data-cols-md="3"' in html
    assert 'data-cols-lg="4"' in html
    assert 'data-cols-xl="5"' in html
    assert 'data-cols-xxl="6"' in html
    assert 'data-span="12"' in html
    assert 'data-span-sm="6"' in html
    assert 'data-span-md="4"' in html
    assert 'data-span-lg="3"' in html
    assert 'data-span-xl="2"' in html
    assert 'data-span-xxl="1"' in html
    assert '<article class="cui-grid-item"' in html


def test_responsive_values_are_snapshotted_into_private_inline_properties():
    html = _render(CGrid(cols=2, sm=3, lg=5, slots={"default": CGridItem(span=2, md=4)}))

    grid = re.search(r'<div[^>]+data-citry-ui-part="grid"[^>]*>', html)
    item = re.search(r'<div[^>]+data-citry-ui-part="grid-item"[^>]*>', html)
    assert grid is not None
    assert item is not None
    assert "--_cui-grid-cols-base: 2;" in grid.group(0)
    assert "--_cui-grid-cols-sm: 3;" in grid.group(0)
    assert "--_cui-grid-cols-lg: 5;" in grid.group(0)
    assert "--_cui-grid-cols-md" not in grid.group(0)
    assert "--_cui-grid-item-span-base: 2;" in item.group(0)
    assert "--_cui-grid-item-span-md: 4;" in item.group(0)


def test_intrinsic_mode_uses_one_plain_length_and_no_count_snapshot():
    html = _render(CGrid(min_col="15.5rem", slots={"default": "Minerals"}))
    root = re.search(r'<div[^>]+data-citry-ui-part="grid"[^>]*>', html)

    assert root is not None
    assert "data-intrinsic" in root.group(0)
    assert 'data-cols="1"' in root.group(0)
    assert "--_cui-grid-min-column-input: 15.5rem;" in root.group(0)
    assert "--_cui-grid-cols-base" not in root.group(0)


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"cols": 0}, ValueError, "between 1 and 12"),
        ({"cols": 13}, ValueError, "between 1 and 12"),
        ({"cols": True}, TypeError, "must be an integer"),
        ({"cols": "2"}, TypeError, "must be an integer"),
        ({"sm": "2"}, TypeError, "must be an integer or None"),
        ({"min_col": 12}, TypeError, "must be a string or None"),
        ({"min_col": "0rem"}, ValueError, "one positive"),
        ({"min_col": "-1rem"}, ValueError, "one positive"),
        ({"min_col": "16%"}, ValueError, "one positive"),
        ({"min_col": "calc(10rem + 1px)"}, ValueError, "one positive"),
        ({"min_col": "16rem; color: red"}, ValueError, "one positive"),
        ({"min_col": "16rem", "cols": 2}, ValueError, "cannot be combined"),
        ({"min_col": "16rem", "lg": 3}, ValueError, "cannot be combined"),
        ({"gap": "xxl"}, ValueError, "gap must be one of"),
        ({"tag": "table"}, ValueError, "tag must be one of"),
        ({"attrs": []}, TypeError, "attrs must be a mapping"),
    ],
)
def test_grid_rejects_invalid_and_conflicting_inputs(kwargs, error, match):
    with pytest.raises(error, match=match):
        _render(CGrid(**kwargs))


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"span": 0}, ValueError, "between 1 and 12"),
        ({"span": 13}, ValueError, "between 1 and 12"),
        ({"span": False}, TypeError, "must be an integer"),
        ({"md": "4"}, TypeError, "must be an integer or None"),
        ({"tag": "nav"}, ValueError, "tag must be one of"),
    ],
)
def test_grid_item_rejects_invalid_inputs(kwargs, error, match):
    with pytest.raises(error, match=match):
        _render(CGridItem(**kwargs))


@pytest.mark.parametrize(
    ("component", "kwargs", "error", "match"),
    [
        (CContainer, {"fluid": 1}, TypeError, "fluid must be a bool"),
        (CContainer, {"fluid": True, "size": "lg"}, ValueError, "non-default size"),
        (CContainer, {"size": "wide"}, ValueError, "size must be one of"),
        (CContainer, {"gutter": "xxl"}, ValueError, "gutter must be one of"),
        (CContainer, {"tag": "header"}, ValueError, "tag must be one of"),
    ],
)
def test_container_rejects_invalid_and_inactive_configuration(component, kwargs, error, match):
    with pytest.raises(error, match=match):
        _render(component(**kwargs))


def test_semantic_roots_and_root_styling_merge():
    html = _render(
        CContainer(
            tag="main",
            size="md",
            gutter="sm",
            class_=["atlas", {"is-ready": True}],
            style={"--cui-container-gutter": "1.25rem"},
            attrs={
                "aria-label": "Mineral atlas",
                "class": "from-attrs",
                "data-atlas": "igneous",
            },
            slots={"default": "Atlas"},
        )
    )

    root = re.search(r'<main[^>]+data-citry-ui-part="container"[^>]*>', html)
    assert root is not None
    assert 'class="cui-container from-attrs atlas is-ready"' in root.group(0)
    assert 'style="--cui-container-gutter: 1.25rem;"' in root.group(0)
    assert 'aria-label="Mineral atlas"' in root.group(0)
    assert 'data-atlas="igneous"' in root.group(0)


@pytest.mark.parametrize(
    ("component", "attribute"),
    [
        (CContainer, "data-size"),
        (CContainer, ":data-fluid"),
        (CGrid, "DATA-COLS"),
        (CGrid, "x-bind:data-cols-lg"),
        (CGridItem, "data-span"),
        (CGridItem, ".data-span-xl"),
        (CGrid, "data-citry-morph"),
        (CGrid, "data-cev-action"),
        (CGrid, "data-cid"),
        (CGrid, "x-bind"),
        (CGrid, "x-bind.modifier"),
        (CGrid, "x-for"),
        (CGrid, "x-if"),
        (CGrid, "x-teleport"),
        (CGrid, "x-ignore"),
        (CGrid, "x-html"),
        (CGrid, "x-text"),
        (CGrid, "x-model"),
    ],
)
def test_roots_reject_owned_runtime_and_structural_attributes(component, attribute):
    with pytest.raises(ValueError, match="cannot"):
        _render(component(attrs={attribute: "consumer"}))


def test_roots_allow_unrelated_targeted_bindings_and_listeners():
    html = _render(
        CGrid(
            attrs={
                "x-data": "{selected: false}",
                ":class": "{selected}",
                "@click": "selected = true",
            }
        )
    )

    assert 'x-data="{selected: false}"' in html
    assert ':class="{selected}"' in html
    assert '@click="selected = true"' in html


def test_css_exposes_breakpoints_variables_and_direct_child_safety_without_javascript():
    css = read_component_source_css("cgrid")

    for width in ("40rem", "48rem", "64rem", "80rem", "96rem"):
        assert f"@media (min-width: {width})" in css
    assert "--cui-container-max-width" in css
    assert "--cui-container-gutter" in css
    assert "--cui-grid-columns" in css
    assert "--cui-grid-gap" in css
    assert "--cui-grid-min-column" in css
    assert "--cui-grid-item-span" in css
    assert ':where([data-citry-ui-part="grid"] > *)' in css
    assert getattr(CContainer, "js", None) is None
    assert getattr(CGrid, "js", None) is None
    assert getattr(CGridItem, "js", None) is None
