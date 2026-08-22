import pytest

import citry_ui
from citry import Citry, Component
from citry_ui.components.ccommand_palette import CCommandPaletteCommand
from citry_ui.quality.asset_report import _family_asset_payloads, _family_assets, asset_report


def _render_split_button_instances(count: int) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class SplitButtonAssetSlice(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {"items": tuple(range(kwargs.count))}

        template = """
          <main>
            <c-for each="item in items">
              <c-CSplitButton
                c-label="f'Actions {item}'"
                c-menu_label="f'More actions {item}'"
              >
                <c-fill name="default">Save {{ item }}</c-fill>
                <c-fill name="menu">
                  <c-CMenuItem c-value="f'copy-{item}'">Copy {{ item }}</c-CMenuItem>
                </c-fill>
              </c-CSplitButton>
            </c-for>
            <c-js />
            <c-css />
          </main>
        """

    return str(SplitButtonAssetSlice(count=count))


def _render_context_menu_instances(count: int) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class ContextMenuAssetSlice(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {"items": tuple(range(kwargs.count))}

        template = """
          <main>
            <c-for each="item in items">
              <c-CContextMenu
                #c-key="item"
                c-id="f'context-menu-asset-{item}'"
                c-aria_label="f'Actions for record {item}'"
              >
                <c-fill name="target" data="{ target_attrs }">
                  <button type="button" c-attrs="target_attrs">Record {{ item }}</button>
                </c-fill>
                <c-fill name="menu">
                  <c-CMenuItem c-value="f'copy-{item}'">Copy {{ item }}</c-CMenuItem>
                </c-fill>
              </c-CContextMenu>
            </c-for>
            <c-js />
            <c-css />
          </main>
        """

    return str(ContextMenuAssetSlice(count=count))


def _render_context_menu_combined_instances(count: int) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class ContextMenuCombinedAssetSlice(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {"items": tuple(range(kwargs.count))}

        template = """
          <main>
            <c-for each="item in items">
              <c-CMenu c-id="f'menu-asset-{item}'">
                <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                  <button
                    type="button"
                    c-disabled="activator_disabled"
                    c-bind="activator_attrs"
                  >Menu {{ item }}</button>
                </c-fill>
                <c-fill name="default">
                  <c-CMenuItem c-value="f'menu-{item}'">Menu action {{ item }}</c-CMenuItem>
                </c-fill>
              </c-CMenu>
              <c-CSplitButton
                c-label="f'Actions {item}'"
                c-menu_label="f'More actions {item}'"
              >
                <c-fill name="default">Save {{ item }}</c-fill>
                <c-fill name="menu">
                  <c-CMenuItem c-value="f'split-{item}'">Split action {{ item }}</c-CMenuItem>
                </c-fill>
              </c-CSplitButton>
              <c-CContextMenu
                c-id="f'context-menu-asset-{item}'"
                c-aria_label="f'Actions for record {item}'"
              >
                <c-fill name="target" data="{ target_attrs }">
                  <button type="button" c-attrs="target_attrs">Record {{ item }}</button>
                </c-fill>
                <c-fill name="menu">
                  <c-CMenuItem c-value="f'context-{item}'">Context action {{ item }}</c-CMenuItem>
                </c-fill>
              </c-CContextMenu>
            </c-for>
            <c-js />
            <c-css />
          </main>
        """

    return str(ContextMenuCombinedAssetSlice(count=count))


def _render_tags_input_instances(count: int) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class TagsInputAssetSlice(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {"items": tuple(range(kwargs.count))}

        template = """
          <main>
            <c-for each="item in items">
              <c-CTagsInput
                #c-key="item"
                c-id="f'tags-input-asset-{item}'"
                c-value="('stable',)"
                c-input_attrs="{'aria-label':'Asset labels'}"
              />
            </c-for>
            <c-js />
            <c-css />
          </main>
        """

    return str(TagsInputAssetSlice(count=count))


def _render_scroll_area_instances(count: int) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class ScrollAreaAssetSlice(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {"items": tuple(range(kwargs.count))}

        template = """
          <main>
            <c-for each="item in items">
              <c-CScrollArea
                #c-key="item"
                c-id="f'scroll-area-asset-{item}'"
                c-aria_label="f'Scroll records {item}'"
              >
                Record {{ item }}
              </c-CScrollArea>
            </c-for>
            <c-js />
            <c-css />
          </main>
        """

    return str(ScrollAreaAssetSlice(count=count))


def _render_image_instances(count: int) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class ImageAssetSlice(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {"items": tuple(range(kwargs.count))}

        template = """
          <main>
            <c-for each="item in items">
              <c-CImage
                #c-key="item"
                src="/quality/image-asset.jpg"
                c-alt="f'Image asset {item}'"
                c-width="640"
                c-height="360"
              />
            </c-for>
            <c-js />
            <c-css />
          </main>
        """

    return str(ImageAssetSlice(count=count))


def _render_command_palette_instances(count: int) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class CommandPaletteAssetSlice(Component):
        citry = app

        class Kwargs:
            count: int

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {
                "items": tuple(range(kwargs.count)),
                "entries": (CCommandPaletteCommand(value="inspect", label="Inspect record"),),
            }

        template = """
          <main>
            <c-for each="item in items">
              <c-CCommandPalette
                #c-key="item"
                c-id="f'command-palette-asset-{item}'"
                c-entries="entries"
                c-label="f'Commands for record {item}'"
              >
                <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                  <c-CButton
                    c-disabled="activator_disabled"
                    c-attrs="activator_attrs"
                  >Commands {{ item }}</c-CButton>
                </c-fill>
              </c-CCommandPalette>
            </c-for>
            <c-js />
            <c-css />
          </main>
        """

    return str(CommandPaletteAssetSlice(count=count))


def test_asset_report_is_deterministic_and_covers_every_family():
    first = asset_report()
    second = asset_report()

    assert first == second
    assert list(first["families"]) == [
        "accordion",
        "disclosure",
        "alert",
        "alert-dialog",
        "avatar",
        "image",
        "skeleton",
        "button",
        "split-button",
        "divider",
        "field-input",
        "file-input",
        "form",
        "tabs",
        "dialog",
        "drawer",
        "popover",
        "tooltip",
        "hover-card",
        "menu",
        "context-menu",
        "toast",
        "combobox",
        "command-palette",
        "table",
        "data-grid",
        "icon",
        "card",
        "carousel",
        "timeline",
        "scroll-area",
        "textarea",
        "native-select",
        "checkbox",
        "button-group",
        "toggle",
        "tag",
        "toolbar",
        "stepper",
        "splitter",
        "tree",
        "pagination",
        "list",
        "listbox",
        "select",
        "multi-select",
        "tags-input",
        "number-input",
        "slider",
        "rating",
        "pin-input",
        "date-input",
        "date-picker",
        "date-range",
        "calendar",
        "time-input",
        "time-picker",
        "navigation-menu",
        "sidebar",
        "tour",
        "editable",
        "virtual-list",
        "transfer-list",
        "form-collection",
        "sortable",
        "infinite-scroll",
        "cascader",
        "tree-grid",
        "color-picker",
    ]
    assert first["catalog"]["limits"] == {
        "javascript": {"raw": 1_114_112, "gzip": 212_992, "brotli": 155_648},
        "css": {"raw": 376_832, "gzip": 49_152, "brotli": 40_960},
    }
    for kind in ("javascript", "css"):
        measurements = first["catalog"][kind]
        limits = first["catalog"]["limits"][kind]
        headroom = first["catalog"]["headroom"][kind]
        assert set(measurements) == {"raw", "gzip", "brotli"}
        assert all(measurements[dimension] > 0 for dimension in measurements)
        assert headroom == {
            dimension: limits[dimension] - measurements[dimension] for dimension in ("raw", "gzip", "brotli")
        }
        assert all(value > 0 for value in headroom.values())
    assert first["families"]["table"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["icon"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["card"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["image"]["javascript"]["raw"] > 0
    assert first["families"]["divider"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["button-group"]["javascript"]["raw"] > 0
    assert first["families"]["split-button"]["javascript"]["raw"] > 0
    assert first["families"]["toggle"]["javascript"]["raw"] > 0
    assert first["families"]["pagination"]["javascript"]["raw"] > 0
    assert first["families"]["number-input"]["javascript"]["raw"] > 0
    assert first["families"]["slider"]["javascript"]["raw"] > 0
    assert first["families"]["pin-input"]["javascript"]["raw"] > 0
    assert first["families"]["date-input"]["javascript"]["raw"] > 0
    assert first["families"]["date-picker"]["javascript"]["raw"] > 0
    assert first["families"]["date-range"]["javascript"]["raw"] > 0
    assert first["families"]["calendar"]["javascript"]["raw"] > 0
    assert first["families"]["time-input"]["javascript"]["raw"] > 0
    assert first["families"]["time-picker"]["javascript"]["raw"] > 0
    assert first["families"]["form-collection"]["javascript"]["raw"] > 0
    assert first["families"]["sortable"]["javascript"]["raw"] > 0
    assert first["families"]["infinite-scroll"]["javascript"]["raw"] > 0
    assert first["families"]["cascader"]["javascript"]["raw"] > 0
    assert first["families"]["tree-grid"]["javascript"]["raw"] > 0
    assert first["families"]["color-picker"]["javascript"]["raw"] > 0
    assert first["families"]["popover"]["javascript"]["raw"] > 0
    assert first["families"]["drawer"]["javascript"]["raw"] > 0
    assert first["families"]["tooltip"]["javascript"]["raw"] > 0
    assert first["families"]["hover-card"]["javascript"]["raw"] > 0
    assert first["families"]["menu"]["javascript"]["raw"] > 0
    assert first["families"]["context-menu"]["javascript"]["raw"] > 0
    assert first["families"]["navigation-menu"]["javascript"]["raw"] > 0
    assert first["families"]["carousel"]["javascript"]["raw"] > 0
    assert first["families"]["scroll-area"]["javascript"]["raw"] > 0
    assert first["families"]["toast"]["javascript"]["raw"] > 0
    assert first["families"]["list"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["tree"]["javascript"]["raw"] > 0
    assert first["families"]["listbox"]["javascript"]["raw"] > 0
    assert first["families"]["multi-select"]["javascript"]["raw"] > 0
    assert first["families"]["tags-input"]["javascript"]["raw"] > 0
    assert first["families"]["editable"]["javascript"]["raw"] > 0
    assert first["families"]["disclosure"]["javascript"]["raw"] > 0


def test_split_button_incremental_assets_stay_within_the_frozen_budget():
    incremental = asset_report()["families"]["split-button"]["incremental"]

    assert incremental["baseline_components"] == ["CButton", "CMenu"]
    assert incremental["javascript"]["gzip"] < 3 * 1024
    assert incremental["css"]["gzip"] < 2 * 1024


def test_tags_input_incremental_assets_stay_within_the_frozen_budget():
    incremental = asset_report()["families"]["tags-input"]["incremental"]

    assert incremental["baseline_components"] == ["CField", "CMultiSelect", "CTag"]
    # Locale-aware interaction announcements and recreated-remove bindings add
    # a bounded client increment; retain explicit headroom below 4.5 KiB.
    assert incremental["javascript"]["gzip"] < 9 * 512
    assert incremental["css"]["gzip"] < 1024


def test_image_assets_stay_within_the_family_budgets():
    family = asset_report()["families"]["image"]
    incremental = family["incremental"]

    assert incremental["baseline_components"] == []
    assert family["javascript"]["raw"] < 32 * 1024
    assert family["javascript"]["gzip"] < int(7.5 * 1024)
    assert family["javascript"]["brotli"] < int(6.5 * 1024)
    assert family["css"]["raw"] < 6 * 1024
    assert family["css"]["gzip"] < int(1.25 * 1024)
    assert family["css"]["brotli"] < 1024


def test_command_palette_assets_stay_within_the_family_budgets():
    family = asset_report()["families"]["command-palette"]
    incremental = family["incremental"]

    assert incremental["baseline_components"] == ["CCombobox", "CDialog"]
    assert incremental["javascript"]["raw"] < 48 * 1024
    assert incremental["javascript"]["gzip"] < 10 * 1024
    assert incremental["javascript"]["brotli"] < 9 * 1024
    assert family["javascript"]["raw"] < 112 * 1024
    assert family["javascript"]["gzip"] < 20 * 1024
    assert family["javascript"]["brotli"] < 17 * 1024
    assert family["css"]["raw"] < 10 * 1024
    assert family["css"]["gzip"] < int(2.25 * 1024)
    assert family["css"]["brotli"] < 2 * 1024


def test_scroll_area_helper_inclusive_assets_stay_within_the_frozen_budget():
    incremental = asset_report()["families"]["scroll-area"]["incremental"]

    assert incremental["baseline_components"] == []
    assert incremental["javascript"]["raw"] < 12 * 1024
    assert incremental["javascript"]["gzip"] < 3 * 1024
    assert incremental["javascript"]["brotli"] < int(2.75 * 1024)
    assert incremental["css"]["raw"] < 6 * 1024
    assert incremental["css"]["gzip"] < int(1.5 * 1024)
    assert incremental["css"]["brotli"] < int(1.25 * 1024)


def test_context_menu_assets_stay_within_the_family_budgets():
    family = asset_report()["families"]["context-menu"]
    incremental = family["incremental"]

    assert incremental["baseline_components"] == ["CMenu", "CSplitButton"]
    assert incremental["javascript"]["raw"] < 32 * 1024
    assert incremental["javascript"]["gzip"] < 10 * 1024
    assert incremental["javascript"]["brotli"] < 9 * 1024
    assert family["javascript"]["raw"] < 160 * 1024
    assert family["javascript"]["gzip"] < 34 * 1024
    assert family["javascript"]["brotli"] < 30 * 1024
    assert family["css"]["raw"] < 20 * 1024
    assert family["css"]["gzip"] < 3 * 1024
    assert family["css"]["brotli"] < int(2.5 * 1024)


def test_scroll_geometry_runtime_is_unique_for_each_family_combination():
    marker = b"incompatible scroll geometry runtime"
    carousel_js, _ = _family_assets(frozenset({"CCarousel", "CCarouselSlide"}))
    scroll_area_js, _ = _family_assets(frozenset({"CScrollArea"}))
    combined_js, _ = _family_assets(frozenset({"CCarousel", "CCarouselSlide", "CScrollArea"}))

    assert carousel_js.count(marker) == 1
    assert scroll_area_js.count(marker) == 1
    assert combined_js.count(marker) == 1


@pytest.mark.parametrize("count", [1, 10, 100])
def test_scroll_area_instance_scaling_emits_each_asset_once(count: int):
    html = _render_scroll_area_instances(count)

    assert html.count("incompatible scroll geometry runtime") == 1
    assert html.count("--_cui-scroll-area-max-block-size:") == 1


@pytest.mark.parametrize("count", [1, 10, 100])
def test_tags_input_instance_scaling_emits_each_component_asset_once(count: int):
    html = _render_tags_input_instances(count)

    assert html.count("citry-ui:form-control-reset-registry") == 1
    assert html.count(":where(.cui-tags-input){") == 1


@pytest.mark.parametrize("count", [1, 10, 100])
def test_image_instance_scaling_emits_each_component_asset_once(count: int):
    html = _render_image_instances(count)

    assert html.count("CImage requires one native image and root") == 1
    assert html.count(":where([data-citry-ui-part=image-root]){") == 1


def test_image_and_avatar_coexist_without_duplicate_image_assets():
    image = _family_asset_payloads(frozenset({"CImage"}))
    avatar = _family_asset_payloads(frozenset({"CAvatar"}))
    combined = _family_asset_payloads(frozenset({"CAvatar", "CImage"}))
    combined_javascript = b"\n".join(combined["js"])
    combined_css = b"\n".join(combined["css"])

    assert combined_javascript.count(b"CImage requires one native image and root") == 1
    assert combined_css.count(b":where([data-citry-ui-part=image-root]){") == 1
    for kind in ("js", "css"):
        assert set(image[kind]) <= set(combined[kind])
        assert set(avatar[kind]) <= set(combined[kind])
        assert all(combined[kind].count(payload) == 1 for payload in set(image[kind] + avatar[kind]))


def test_shared_secondary_runtime_is_counted_once_per_measured_slice():
    marker = b"cannot replace an incompatible anchored-layer runtime"
    popover_js, _ = _family_assets(frozenset({"CPopover"}))
    mixed_js, _ = _family_assets(frozenset({"CPopover", "CTooltip", "CMenu"}))

    assert popover_js.count(marker) == 1
    assert mixed_js.count(marker) == 1


def test_split_button_coexists_with_one_copy_of_each_shared_runtime():
    javascript, _ = _family_assets(frozenset({"CButton", "CMenu", "CSplitButton"}))

    assert javascript.count(b"cannot replace an incompatible anchored-layer runtime") == 1
    assert javascript.count(b"cannot replace an incompatible CButton runtime") == 1
    assert javascript.count(b"cannot replace an incompatible CMenu runtime") == 1
    assert javascript.count(b"cannot replace an incompatible SplitButton submit runtime") == 1


def test_context_menu_coexists_with_one_copy_of_each_shared_menu_runtime():
    javascript, _ = _family_assets(frozenset({"CMenu", "CSplitButton", "CContextMenu"}))

    assert javascript.count(b"cannot replace an incompatible anchored-layer runtime") == 1
    assert javascript.count(b"cannot replace an incompatible CMenu runtime") == 1
    assert javascript.count(b"CContextMenu requires the compatible external Menu controller") == 1


@pytest.mark.parametrize("count", [1, 10, 100])
def test_split_button_instance_scaling_emits_each_shared_asset_once(count: int):
    html = _render_split_button_instances(count)

    assert html.count("cannot replace an incompatible anchored-layer runtime") == 1
    assert html.count("cannot replace an incompatible CButton runtime") == 1
    assert html.count("cannot replace an incompatible CMenu runtime") == 1
    assert html.count("cannot replace an incompatible SplitButton submit runtime") == 1
    assert html.count("@keyframes cui-button-spin") == 1
    assert html.count(":where(.cui-menu-host) {") == 1


@pytest.mark.parametrize("count", [1, 10, 100])
def test_context_menu_instance_scaling_emits_each_shared_asset_once(count: int):
    html = _render_context_menu_instances(count)

    assert html.count("cannot replace an incompatible anchored-layer runtime") == 1
    assert html.count("cannot replace an incompatible CMenu runtime") == 1
    assert html.count("CContextMenu requires the compatible external Menu controller") == 1
    assert html.count(":where(.cui-menu-host) {") == 1
    assert html.count(":where(.cui-context-menu-host) {") == 1


@pytest.mark.parametrize("count", [1, 10, 100])
def test_context_menu_combined_scaling_emits_each_shared_asset_once(count: int):
    html = _render_context_menu_combined_instances(count)

    assert html.count("cannot replace an incompatible anchored-layer runtime") == 1
    assert html.count("cannot replace an incompatible CButton runtime") == 1
    assert html.count("cannot replace an incompatible CMenu runtime") == 1
    assert html.count("cannot replace an incompatible SplitButton submit runtime") == 1
    assert html.count("CContextMenu requires the compatible external Menu controller") == 1
    assert html.count("@keyframes cui-button-spin") == 1
    assert html.count(":where(.cui-split-button) {") == 1
    assert html.count(":where(.cui-menu-host) {") == 1
    assert html.count(":where(.cui-context-menu-host) {") == 1


def test_command_palette_coexists_with_one_copy_of_each_shared_runtime():
    javascript, _ = _family_assets(frozenset({"CCommandPalette", "CCombobox", "CDialog"}))

    assert javascript.count(b"cannot replace an incompatible anchored-layer runtime") == 1
    assert javascript.count(b"cannot replace an incompatible Dialog controller") == 1
    assert javascript.count(b"cannot replace an incompatible active-descendant runtime") == 1
    assert javascript.count(b"CCommandPalette private runtime dependency did not load") == 1


@pytest.mark.parametrize("count", [1, 10, 100])
def test_command_palette_instance_scaling_emits_each_shared_asset_once(count: int):
    html = _render_command_palette_instances(count)

    assert html.count("cannot replace an incompatible anchored-layer runtime") == 1
    assert html.count("cannot replace an incompatible Dialog controller") == 1
    assert html.count("cannot replace an incompatible active-descendant runtime") == 1
    assert html.count("CCommandPalette private runtime dependency did not load") == 1
    assert html.count(":where(.cui-command-palette-host) {") == 1
