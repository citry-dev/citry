import pytest

import citry_ui
from citry import Citry, Component
from citry_ui.components.ccommand_palette import CCommandPaletteCommand
from citry_ui.quality.asset_report import (
    _command_palette_attribution,
    _family_asset_payloads,
    _family_assets,
    _validate_marker_ownership,
    asset_report,
)

_CONTEXT_MENU_PROVENANCE = {
    "context_javascript_source": {
        "sha256": "d74fd1adf4be44ed687c4753633a1e46c900b8d0710b58a5c4802a18a4bc4315",
        "raw": 28_081,
        "gzip": 9_088,
        "brotli": 8_262,
    },
    "context_css_source": {
        "sha256": "22979cafffdd6a575000af38ba46f75bab8eed45c72bd7f2351b02d53eaf603a",
        "raw": 575,
        "gzip": 257,
        "brotli": 193,
    },
    "menu_runtime_before_context": {
        "sha256": "1c44a9bbc35186fdcabb1a0e7f9f23e62f4743c462614a4fb33c8f65bafb4116",
        "raw": 82_023,
        "gzip": 15_494,
        "brotli": 12_999,
    },
    "menu_runtime_after_context": {
        "sha256": "cf6d144c5b4fe322010e8c02d35ac4581cecbcb0bb4721de527abde47f473178",
        "raw": 85_640,
        "gzip": 16_142,
        "brotli": 13_538,
    },
    "anchored_layer_before_context": {
        "sha256": "ca5ab04ec15f4abaa17a6878ea209e0165175cae0188b0c058d64f1273682624",
        "raw": 29_168,
        "gzip": 5_521,
        "brotli": 4_803,
    },
    "anchored_layer_after_context": {
        "sha256": "a695ff7cd36c37848769a072084679de0c815928a1eddd234a55fcd4fef9a3e2",
        "raw": 29_514,
        "gzip": 5_598,
        "brotli": 4_871,
    },
}

_CONTEXT_MENU_FRAME_SLICES = {
    "menu-only": {
        "js": (
            {
                "sha256": "c35aff2b5e584b305e762d254c74f0903f20d346bdff1c3a0a2096c3f740c687",
                "raw": 210,
                "gzip": 179,
                "brotli": 152,
            },
            {
                "sha256": "fa492f777a1752e9b6671f69d92bc3aa4983ee68f7bdfda489388f5b85fa2469",
                "raw": 30_395,
                "gzip": 5_712,
                "brotli": 4_977,
            },
            {
                "sha256": "a0ecd20118f4ec8b07280366fbe8181c683c27fdc8e7cacabb12acc92a864c28",
                "raw": 85_660,
                "gzip": 16_149,
                "brotli": 13_550,
            },
        ),
        "css": (
            {
                "sha256": "b3a471c2aaa887b77d82302fa01a3406cfd0153a312ee521c43caca16652f3b3",
                "raw": 15_909,
                "gzip": 2_435,
                "brotli": 2_117,
            },
        ),
    },
    "split-button-only": {
        "js": (
            {
                "sha256": "e8f5387e21b37035329f1e53f4d765e048dcaa9ab453141cb4e80c27cf03ad3c",
                "raw": 5_982,
                "gzip": 1_734,
                "brotli": 1_483,
            },
            {
                "sha256": "fa492f777a1752e9b6671f69d92bc3aa4983ee68f7bdfda489388f5b85fa2469",
                "raw": 30_395,
                "gzip": 5_712,
                "brotli": 4_977,
            },
            {
                "sha256": "f6ba3176116e72634495e6b1a296643dcb533cfdb38e6d40547973847e3e6502",
                "raw": 8_846,
                "gzip": 2_182,
                "brotli": 1_876,
            },
            {
                "sha256": "a0ecd20118f4ec8b07280366fbe8181c683c27fdc8e7cacabb12acc92a864c28",
                "raw": 85_660,
                "gzip": 16_149,
                "brotli": 13_550,
            },
            {
                "sha256": "4312df6597556eb197b307929426fd570a1642734ebba9ec4d7e7e38393884b1",
                "raw": 5_356,
                "gzip": 1_370,
                "brotli": 1_169,
            },
        ),
        "css": (
            {
                "sha256": "156d5f03d9c5000863d0b910c74d05eec18b19728a35b8e076ff2c629d6c7850",
                "raw": 2_107,
                "gzip": 609,
                "brotli": 508,
            },
            {
                "sha256": "58b9af1dcb4a0d9b6b09ab1bbdee94437e2d8d84820f47e274a29de26517a461",
                "raw": 9_819,
                "gzip": 1_586,
                "brotli": 1_353,
            },
            {
                "sha256": "b3a471c2aaa887b77d82302fa01a3406cfd0153a312ee521c43caca16652f3b3",
                "raw": 15_909,
                "gzip": 2_435,
                "brotli": 2_117,
            },
        ),
    },
    "context-menu-only": {
        "js": (
            {
                "sha256": "50f4a76c059a2893a3e88e875e7c333745555b11c917e0313eafd1b5363166db",
                "raw": 27_159,
                "gzip": 9_021,
                "brotli": 8_186,
            },
            {
                "sha256": "fa492f777a1752e9b6671f69d92bc3aa4983ee68f7bdfda489388f5b85fa2469",
                "raw": 30_395,
                "gzip": 5_712,
                "brotli": 4_977,
            },
            {
                "sha256": "a0ecd20118f4ec8b07280366fbe8181c683c27fdc8e7cacabb12acc92a864c28",
                "raw": 85_660,
                "gzip": 16_149,
                "brotli": 13_550,
            },
        ),
        "css": (
            {
                "sha256": "d6b81c103af87b1eceb56ca7326a4640f8c4bb9b914faf830f4cb7cd2a70488e",
                "raw": 439,
                "gzip": 247,
                "brotli": 179,
            },
            {
                "sha256": "b3a471c2aaa887b77d82302fa01a3406cfd0153a312ee521c43caca16652f3b3",
                "raw": 15_909,
                "gzip": 2_435,
                "brotli": 2_117,
            },
        ),
    },
    "combined": {
        "js": (
            {
                "sha256": "e8f5387e21b37035329f1e53f4d765e048dcaa9ab453141cb4e80c27cf03ad3c",
                "raw": 5_982,
                "gzip": 1_734,
                "brotli": 1_483,
            },
            {
                "sha256": "fa492f777a1752e9b6671f69d92bc3aa4983ee68f7bdfda489388f5b85fa2469",
                "raw": 30_395,
                "gzip": 5_712,
                "brotli": 4_977,
            },
            {
                "sha256": "f6ba3176116e72634495e6b1a296643dcb533cfdb38e6d40547973847e3e6502",
                "raw": 8_846,
                "gzip": 2_182,
                "brotli": 1_876,
            },
            {
                "sha256": "a0ecd20118f4ec8b07280366fbe8181c683c27fdc8e7cacabb12acc92a864c28",
                "raw": 85_660,
                "gzip": 16_149,
                "brotli": 13_550,
            },
            {
                "sha256": "4312df6597556eb197b307929426fd570a1642734ebba9ec4d7e7e38393884b1",
                "raw": 5_356,
                "gzip": 1_370,
                "brotli": 1_169,
            },
            {
                "sha256": "c35aff2b5e584b305e762d254c74f0903f20d346bdff1c3a0a2096c3f740c687",
                "raw": 210,
                "gzip": 179,
                "brotli": 152,
            },
            {
                "sha256": "50f4a76c059a2893a3e88e875e7c333745555b11c917e0313eafd1b5363166db",
                "raw": 27_159,
                "gzip": 9_021,
                "brotli": 8_186,
            },
        ),
        "css": (
            {
                "sha256": "156d5f03d9c5000863d0b910c74d05eec18b19728a35b8e076ff2c629d6c7850",
                "raw": 2_107,
                "gzip": 609,
                "brotli": 508,
            },
            {
                "sha256": "58b9af1dcb4a0d9b6b09ab1bbdee94437e2d8d84820f47e274a29de26517a461",
                "raw": 9_819,
                "gzip": 1_586,
                "brotli": 1_353,
            },
            {
                "sha256": "b3a471c2aaa887b77d82302fa01a3406cfd0153a312ee521c43caca16652f3b3",
                "raw": 15_909,
                "gzip": 2_435,
                "brotli": 2_117,
            },
            {
                "sha256": "d6b81c103af87b1eceb56ca7326a4640f8c4bb9b914faf830f4cb7cd2a70488e",
                "raw": 439,
                "gzip": 247,
                "brotli": 179,
            },
        ),
    },
}

_IMAGE_PROVENANCE = {
    "javascript_source": {
        "sha256": "75b74be92b6761ef0c2194474eefc0e99e69ef409b79037b4c61caf47ef36f53",
        "raw": 31_583,
        "gzip": 6_534,
        "brotli": 5_734,
    },
    "css_source": {
        "sha256": "113c53abe2c901f3858e9bb6faad27d003da53c857adc2f984e38b9fbd0359e6",
        "raw": 3_063,
        "gzip": 680,
        "brotli": 553,
    },
    "terser_lower_bound": {
        "sha256": "7d7e133da45731d825bf47c13ea83157b5dc5ecfaeb47a4928ffecab2b859b35",
        "raw": 13_361,
        "gzip": 4_705,
        "brotli": 4_209,
    },
}

_COMMAND_PALETTE_MARKER_SLICES = (
    ("initializer", "8798500a6daf09ef5c6ea2ae12128b504e69009c94b9d2d6ef799f84b969c731", 38_163, 8_069, 7_076),
    (
        "dialog-layer-preparation",
        "f546714412b15bc9bc03e1e0cfbab623fac4ba6a66eb0a339c01cb146842257a",
        850,
        385,
        308,
    ),
    (
        "dialog-document-lock-state",
        "8915078664595b1831407306a06a7d63289feebea10913963ccadbbc6c9d29e7",
        194,
        129,
        102,
    ),
    ("dialog-handoff-keys", "e5090b2285cfa12fbdadc9183773931a0f57d222e35ce5dd9829b287a951ae69", 281, 151, 129),
    (
        "dialog-root-scope-state",
        "700056c404db3d445f6735e2f71ddeb80e171c08e9b8b8d60123a99c4c250c32",
        713,
        319,
        266,
    ),
    ("dialog-document-lock", "4fd95ef4939f6bdc566aea6560f4ebcb4f297bce2aa1eec4c8e9b8992dcc7688", 1_585, 534, 435),
    (
        "dialog-root-scope-manager",
        "a24c21d8b734380631e49a34109b26425753ca2b2c0de2ebef979b6329ca1bd5",
        911,
        379,
        316,
    ),
    (
        "dialog-handoff-close-state",
        "45f7dde61337c29f0b9eef6ee7516cd82a83001433505a95c57cd86185b983dd",
        261,
        140,
        112,
    ),
    ("dialog-focus-target", "a4ef28977e3749ef7727212a171da2be377ca0527c2b3b0e2fc66fe57875aea5", 200, 133, 108),
    (
        "dialog-handoff-consume",
        "e0d47db9ecf279fc9534220079fb12db7952cf3c5f981557fbc74639fd901e08",
        1_450,
        465,
        392,
    ),
    ("dialog-focus-hooks", "570fc52b3affaccca3e3f7fdd6470ab6b4a6220fd30b3775fcbe815bc11aa719", 494, 265, 214),
    (
        "dialog-focus-restore",
        "127f781c297f64eae55687bd40fb9610255183a6267701e13e814715f66b1145",
        832,
        345,
        277,
    ),
    (
        "dialog-handoff-close-intent",
        "0968552314616b9e895f435df9b0cd251b2b3848d82e9929a0c34e509480704e",
        297,
        188,
        155,
    ),
    (
        "dialog-handoff-close-expected",
        "f05963be04725f9600eded70df5a0e2deb60490430c98a98f6480b0d4df3bbf6",
        203,
        127,
        100,
    ),
    (
        "dialog-handoff-close-reclaim",
        "b03bdc2b5c1ea068e26b8f017f7eb55ebd726017288a84b377da600f14e034ae",
        610,
        273,
        215,
    ),
    (
        "dialog-handoff-close-retire",
        "91438cfb95a7036687bbd5bf10a8198d56cb66db93eddbd9ec1ba9baf240294a",
        195,
        124,
        97,
    ),
    (
        "dialog-root-scope-refresh",
        "c179e45501c20cd2170f2fd655c79f63dd541624cd1845e2ade7bff81c76bfbb",
        1_120,
        395,
        333,
    ),
    (
        "dialog-handoff-close-listener",
        "b7af13d89b1be1e8fe6e914b7b720e1bd6a69fe12aef7eafd5a8af81ef061425",
        224,
        144,
        116,
    ),
    (
        "dialog-handoff-close-cleanup",
        "f9946ec657223c5c69751fcaa20c38141af57e91d0a578a3375b5fbcacfc1125",
        332,
        170,
        149,
    ),
    (
        "dialog-handoff-close-unlisten",
        "f9e8f61c38e1f55f024e42775dfb69c6013373d4823f8e2c56f554a162835a2e",
        231,
        148,
        121,
    ),
    (
        "dialog-handoff-produce",
        "8dd79fa974a41e758f4cf2a75d8eda2c24156a500e7c2f87074bd6fdf28ac4d1",
        1_153,
        441,
        367,
    ),
    ("dialog-handoff-abort", "7cd757fca5f55f135041a6beac3fa0d1c067bb318fce616183562b436cc1fc7f", 441, 227, 189),
    ("active-owner-key", "63e82480940b1925753a78ded09ea21b73d6c31eac81732d2c1eb4ed48c511fa", 202, 138, 114),
    (
        "active-owner-transfer",
        "870ff916fed2f2d1f3799711f185b6e64c58657f27eb0a54de76ee980ad8e0dd",
        888,
        362,
        319,
    ),
    (
        "active-neighbor-handoff",
        "e4e2bfe18026764575219524edcf7de05e7df2e18acb1b2e40be56c5562aad6b",
        968,
        379,
        317,
    ),
    (
        "active-group-registration",
        "dd91e18fbd56fb6b393d3c69780c499defa5969062514fe14ecba7d592985d5d",
        377,
        198,
        159,
    ),
    (
        "active-owner-cleanup",
        "5b40c7c87725629103816ac29dac224128dd8a8f5deffb989b5c113a0c8bd874",
        318,
        181,
        141,
    ),
)


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
        "icon",
        "card",
        "carousel",
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
        "navigation-menu",
        "editable",
    ]
    assert first["catalog"] == {
        "javascript": {
            "sha256": "b094f8784feea6a46769c029c12fe0177e41b7490f306acec556a065ffb7c27d",
            "raw": 860_594,
            "gzip": 162_564,
            "brotli": 116_820,
        },
        "css": {
            "sha256": "f2806359ebdf9751cbf33ccc0b3afcfa9180aabebdb879f70be117ec3ade527e",
            "raw": 297_478,
            "gzip": 35_877,
            "brotli": 28_241,
        },
        "limits": {
            "javascript": {"raw": 983_040, "gzip": 196_608, "brotli": 131_072},
            "css": {"raw": 344_064, "gzip": 40_960, "brotli": 32_768},
        },
        "headroom": {
            "javascript": {"raw": 122_446, "gzip": 34_044, "brotli": 14_252},
            "css": {"raw": 46_586, "gzip": 5_083, "brotli": 4_527},
        },
    }
    assert first["families"]["table"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["icon"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["card"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["image"]["javascript"]["raw"] > 0
    assert first["families"]["divider"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["button-group"]["javascript"]["raw"] > 0
    assert first["families"]["split-button"]["javascript"]["raw"] > 0
    assert first["families"]["toggle"]["javascript"]["raw"] > 0
    assert first["families"]["pagination"]["javascript"]["raw"] > 0
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


def test_image_exact_frames_and_zero_shared_delta_stay_within_the_frozen_budget():
    family = asset_report()["families"]["image"]
    incremental = family["incremental"]
    attribution = family["attribution"]

    assert incremental["baseline_components"] == []
    assert attribution == {
        "provenance": _IMAGE_PROVENANCE,
        "emitted": {
            "js": (
                {
                    "sha256": "1eef1045a3f8bc7ef38b86b7f782ea7772e3dfcc67f4cd20293fe7888dadf16f",
                    "raw": 27_667,
                    "gzip": 6_405,
                    "brotli": 5_613,
                },
            ),
            "css": (
                {
                    "sha256": "f7e03915e4a116346f90f6f1cc130079daf15b15a0b784658a9225f08bd8c158",
                    "raw": 2_639,
                    "gzip": 665,
                    "brotli": 540,
                },
            ),
        },
        "shared_positive_delta": {
            "javascript": {"raw": 0, "gzip": 0, "brotli": 0},
            "css": {"raw": 0, "gzip": 0, "brotli": 0},
        },
        "charged": {
            "javascript": {"raw": 27_667, "gzip": 6_405, "brotli": 5_613},
            "css": {"raw": 2_639, "gzip": 665, "brotli": 540},
        },
    }
    assert incremental["javascript"]["raw"] < 32 * 1024
    assert incremental["javascript"]["gzip"] < int(7.5 * 1024)
    assert incremental["javascript"]["brotli"] < int(6.5 * 1024)
    assert incremental["css"]["raw"] < 6 * 1024
    assert incremental["css"]["gzip"] < int(1.25 * 1024)
    assert incremental["css"]["brotli"] < 1024


def test_command_palette_exact_attribution_and_standalone_assets_stay_within_the_frozen_budget():
    attribution = asset_report()["families"]["command-palette"]["attribution"]

    assert attribution["provenance"] == {
        "javascript_source": {
            "sha256": "8ba0eba3a70430a2a9847c782dbe1c78b846317db9711d76ef7d95ed3021be00",
            "raw": 44_313,
            "gzip": 8_227,
            "brotli": 7_217,
        },
        "css_source": {
            "sha256": "db5eb273fc0b0639c4a033031e235f581fc33d8b6a7339b6625db4360d4cbab4",
            "raw": 11_440,
            "gzip": 1_797,
            "brotli": 1_539,
        },
        "shared_source_freeze": {
            "citry_ui.components.cdialog.cdialog": (
                "21560ee8b89e73feba2f6800f149523a61de0a3f332d1aad60c40136fd7d84e4"
            ),
            "citry_ui.components.ccombobox.ccombobox": (
                "447c48f29ca4626d238e966ad1aaef85e5565abfa2aabed1c1143304c81c5257"
            ),
            "citry_ui.components._dialog_controller": (
                "5439f917d4918c8926ee82f0a33056ae58d4f2a0b2c7bd903308df37b9c157c3"
            ),
            "citry_ui.components._active_descendant": (
                "041544b5de5f5d59bc8ca8d5910516347f27c2e2591a48aca7c7f27d409766c6"
            ),
            "citry_ui.components._anchored_layer": (
                "7a27e4491359af9a4f916726e1423d1fd846fe55e9be24063748c2d8798f9694"
            ),
        },
    }
    assert attribution["emitted"] == {
        "js": (
            {
                "sha256": "9e212dd9eba9c5d9439d0c273c4dd8e1db6c993d8c0757384c9de5e62744f185",
                "raw": 38_165,
                "gzip": 8_071,
                "brotli": 7_074,
            },
            {
                "sha256": "fa492f777a1752e9b6671f69d92bc3aa4983ee68f7bdfda489388f5b85fa2469",
                "raw": 30_395,
                "gzip": 5_712,
                "brotli": 4_977,
            },
            {
                "sha256": "066105ceba93c5a425b798e3f1ebf6606a0784ad79f89537e9c4c86a60737789",
                "raw": 22_763,
                "gzip": 4_750,
                "brotli": 4_146,
            },
            {
                "sha256": "f6eb4fbff815f87208ec3690db4546ef800673b27ef689c2551a795f9dced8b7",
                "raw": 6_876,
                "gzip": 1_892,
                "brotli": 1_625,
            },
        ),
        "css": (
            {
                "sha256": "b969aee04a8dda0f9bb3f8d067375de3fa10093948fc706afa3494ad82bde0c8",
                "raw": 9_714,
                "gzip": 1_760,
                "brotli": 1_523,
            },
        ),
    }
    assert (
        tuple(
            (entry["marker"], entry["sha256"], entry["raw"], entry["gzip"], entry["brotli"])
            for entry in attribution["marker_slices"]["javascript"]
        )
        == _COMMAND_PALETTE_MARKER_SLICES
    )
    assert attribution["marker_slices"]["css"] == (
        {
            "marker": "css",
            "sha256": "cb33b3d988f130cbf726d72ba8fbd1428a0d5d22cb069283daa054bc92f6a076",
            "raw": 9_712,
            "gzip": 1_760,
            "brotli": 1_508,
        },
    )
    assert attribution["attributed"] == {
        "javascript": {
            "sha256": "62630986d4f4dd0e8613b77abc90a213194fc3dfb32b80ae4035dc83d15f2305",
            "raw": 53_493,
            "gzip": 10_685,
            "brotli": 9_208,
        },
        "css": {
            "sha256": "cb33b3d988f130cbf726d72ba8fbd1428a0d5d22cb069283daa054bc92f6a076",
            "raw": 9_712,
            "gzip": 1_760,
            "brotli": 1_508,
        },
    }
    assert attribution["shared_foundations"] == {
        "dialog": {
            "baseline": {
                "sha256": "17b49a6cc706860b32316c42c6d4822e1d85f245e508e9af07995933d2ca50db",
                "raw": 17_870,
                "gzip": 4_327,
                "brotli": 3_723,
            },
            "sha256": "5ea7c89e58a908b74d897061f7b60170cedfb6ff87322ecd0a10234701440c05",
            "current": {"raw": 21_442, "gzip": 4_899, "brotli": 4_273},
            "positive_delta": {"raw": 3_572, "gzip": 572, "brotli": 550},
        },
        "anchored-layer": {
            "baseline": {
                "sha256": "dcdb81484caa8915fda8df0496f69ee32bfb60f73a991620626bdf9b0b190951",
                "raw": 29_534,
                "gzip": 5_607,
                "brotli": 4_882,
            },
            "sha256": "b4f93fb285d6bfe031fa04dffd2ef9b1b03436ed3b5cbb45eb80a1f46fafe909",
            "current": {"raw": 29_545, "gzip": 5_608, "brotli": 4_884},
            "positive_delta": {"raw": 11, "gzip": 1, "brotli": 2},
        },
        "combobox": {
            "baseline": {
                "sha256": "f1d24c5827e40c9990542b61375ab8aaa880b0703818bca1506df8cf760f078e",
                "raw": 38_243,
                "gzip": 7_596,
                "brotli": 6_648,
            },
            "sha256": "370baa4ef03119b3b1981c5dac6370a8ccc91b0db35c8938728955679605400f",
            "current": {"raw": 41_955, "gzip": 8_652, "brotli": 7_507},
            "positive_delta": {"raw": 3_712, "gzip": 1_056, "brotli": 859},
        },
    }
    assert attribution["shared_positive_delta"] == {
        "javascript": {"raw": 7_295, "gzip": 1_629, "brotli": 1_411},
        "css": {"raw": 0, "gzip": 0, "brotli": 0},
    }
    assert attribution["charged"] == {
        "javascript": {"raw": 60_788, "gzip": 12_314, "brotli": 10_619},
        "css": {"raw": 9_712, "gzip": 1_760, "brotli": 1_508},
    }
    assert attribution["standalone"] == {
        "javascript": {
            "sha256": "3e87497507aef85e3ff4b8f7d726283f734356f856f72f5a0ab1335a81150831",
            "raw": 98_199,
            "gzip": 18_754,
            "brotli": 15_948,
        },
        "css": {
            "sha256": "b969aee04a8dda0f9bb3f8d067375de3fa10093948fc706afa3494ad82bde0c8",
            "raw": 9_714,
            "gzip": 1_760,
            "brotli": 1_523,
        },
    }
    assert attribution["charged"]["javascript"]["raw"] < 65_536
    assert attribution["charged"]["javascript"]["gzip"] < 13_312
    assert attribution["charged"]["javascript"]["brotli"] < 11_264
    assert attribution["charged"]["css"]["raw"] < 10_240
    assert attribution["charged"]["css"]["gzip"] < 2_304
    assert attribution["charged"]["css"]["brotli"] < 2_048
    assert attribution["standalone"]["javascript"]["raw"] < 114_688
    assert attribution["standalone"]["javascript"]["gzip"] < 20_480
    assert attribution["standalone"]["javascript"]["brotli"] < 17_408


def test_command_palette_marker_parser_rejects_missing_unknown_and_overlapping_blocks():
    with pytest.raises(ValueError, match="ownership set"):
        _validate_marker_ownership((b"",), ("one",))
    with pytest.raises(ValueError, match="ownership set"):
        _validate_marker_ownership(
            (b"/* citry-ui:command-palette-attribution:unknown:begin */",),
            (),
        )
    with pytest.raises(ValueError, match="overlap"):
        _validate_marker_ownership(
            (
                b"/* citry-ui:command-palette-attribution:one:begin */"
                b"/* citry-ui:command-palette-attribution:two:begin */"
                b"/* citry-ui:command-palette-attribution:one:end */"
                b"/* citry-ui:command-palette-attribution:two:end */",
            ),
            ("one", "two"),
        )


def test_command_palette_live_shared_frame_drift_cannot_keep_the_frozen_charge_green():
    command = _family_asset_payloads(frozenset({"CCommandPalette"}))
    dialog = _family_asset_payloads(frozenset({"CDialog"}))
    combobox = _family_asset_payloads(frozenset({"CCombobox"}))
    baseline = _command_palette_attribution(command, dialog, combobox)

    mutated_dialog = {**dialog, "js": (dialog["js"][0] + b"x", *dialog["js"][1:])}
    adapter_change = _command_palette_attribution(command, mutated_dialog, combobox)
    assert adapter_change["attributed"] == baseline["attributed"]
    assert adapter_change["shared_foundations"]["dialog"]["current"]["raw"] == 21_443
    assert adapter_change["shared_foundations"]["dialog"]["positive_delta"]["raw"] == 3_573
    assert adapter_change["charged"]["javascript"]["raw"] == baseline["charged"]["javascript"]["raw"] + 1

    marker = b"/* citry-ui:command-palette-attribution:dialog-document-lock-state:begin */"
    helper_index = next(index for index, payload in enumerate(command["js"]) if marker in payload)
    helper = command["js"][helper_index]
    insert_at = helper.index(marker) + len(marker)
    mutated_helper = helper[:insert_at] + b"x" + helper[insert_at:]
    mutated_command = {
        **command,
        "js": (*command["js"][:helper_index], mutated_helper, *command["js"][helper_index + 1 :]),
    }
    attributed_change = _command_palette_attribution(mutated_command, dialog, combobox)

    assert attributed_change["attributed"]["javascript"]["raw"] == baseline["attributed"]["javascript"]["raw"] + 1
    assert attributed_change["shared_foundations"] == baseline["shared_foundations"]
    assert attributed_change["charged"]["javascript"]["raw"] == baseline["charged"]["javascript"]["raw"] + 1

    unmarked_helper = helper + b"x"
    unmarked_command = {
        **command,
        "js": (*command["js"][:helper_index], unmarked_helper, *command["js"][helper_index + 1 :]),
    }
    helper_change = _command_palette_attribution(unmarked_command, dialog, combobox)
    assert helper_change["attributed"] == baseline["attributed"]
    assert helper_change["shared_foundations"]["dialog"]["current"]["raw"] == 21_443
    assert helper_change["shared_foundations"]["dialog"]["positive_delta"]["raw"] == 3_573
    assert helper_change["charged"]["javascript"]["raw"] == baseline["charged"]["javascript"]["raw"] + 1


def test_scroll_area_helper_inclusive_assets_stay_within_the_frozen_budget():
    incremental = asset_report()["families"]["scroll-area"]["incremental"]

    assert incremental["baseline_components"] == []
    assert incremental["javascript"]["raw"] < 12 * 1024
    assert incremental["javascript"]["gzip"] < 3 * 1024
    assert incremental["javascript"]["brotli"] < int(2.75 * 1024)
    assert incremental["css"]["raw"] < 6 * 1024
    assert incremental["css"]["gzip"] < int(1.5 * 1024)
    assert incremental["css"]["brotli"] < int(1.25 * 1024)


def test_context_menu_attributed_assets_stay_within_the_frozen_budget():
    family = asset_report()["families"]["context-menu"]
    incremental = family["incremental"]
    attribution = family["attribution"]

    assert incremental["baseline_components"] == ["CMenu", "CSplitButton"]
    assert attribution["provenance"] == _CONTEXT_MENU_PROVENANCE
    assert attribution["adapter"] == {
        "javascript": {
            "sha256": "50f4a76c059a2893a3e88e875e7c333745555b11c917e0313eafd1b5363166db",
            "raw": 27_159,
            "gzip": 9_021,
            "brotli": 8_186,
        },
        "css": {
            "sha256": "d6b81c103af87b1eceb56ca7326a4640f8c4bb9b914faf830f4cb7cd2a70488e",
            "raw": 439,
            "gzip": 247,
            "brotli": 179,
        },
    }
    assert attribution["shared_positive_delta"] == {
        "javascript": {"raw": 3_963, "gzip": 725, "brotli": 607},
        "css": {"raw": 0, "gzip": 0, "brotli": 0},
    }
    assert attribution["charged"] == {
        "javascript": {"raw": 31_122, "gzip": 9_746, "brotli": 8_793},
        "css": {"raw": 439, "gzip": 247, "brotli": 179},
    }
    assert attribution["charged"]["javascript"]["raw"] < 32 * 1024
    assert attribution["charged"]["javascript"]["gzip"] < 10 * 1024
    assert attribution["charged"]["javascript"]["brotli"] < 9 * 1024
    assert attribution["charged"]["css"]["gzip"] < 512


def test_context_menu_asset_frames_match_the_frozen_shared_delta_evidence():
    attribution = asset_report()["families"]["context-menu"]["attribution"]

    assert attribution["frame_slices"] == _CONTEXT_MENU_FRAME_SLICES


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
    assert html.count(':where([data-citry-ui-part="image-root"]) {') == 1


def test_image_and_avatar_coexist_without_duplicate_image_assets():
    image = _family_asset_payloads(frozenset({"CImage"}))
    avatar = _family_asset_payloads(frozenset({"CAvatar"}))
    combined = _family_asset_payloads(frozenset({"CAvatar", "CImage"}))
    combined_javascript = b"\n".join(combined["js"])
    combined_css = b"\n".join(combined["css"])

    assert combined_javascript.count(b"CImage requires one native image and root") == 1
    assert combined_css.count(b':where([data-citry-ui-part="image-root"]) {') == 1
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
    assert html.count("citry-ui:command-palette-attribution:css:begin") == 1
