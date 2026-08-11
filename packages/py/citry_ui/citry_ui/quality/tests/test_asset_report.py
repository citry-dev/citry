from citry_ui.quality.asset_report import _family_assets, asset_report


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
        "skeleton",
        "button",
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
        "toast",
        "combobox",
        "table",
        "icon",
        "card",
        "carousel",
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
        "navigation-menu",
        "editable",
    ]
    assert first["catalog"]["javascript"]["brotli"] <= 80 * 1024
    assert first["catalog"]["css"]["brotli"] <= 30 * 1024
    assert first["families"]["table"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["icon"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["card"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["divider"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["button-group"]["javascript"]["raw"] > 0
    assert first["families"]["toggle"]["javascript"]["raw"] > 0
    assert first["families"]["pagination"]["javascript"]["raw"] > 0
    assert first["families"]["popover"]["javascript"]["raw"] > 0
    assert first["families"]["drawer"]["javascript"]["raw"] > 0
    assert first["families"]["tooltip"]["javascript"]["raw"] > 0
    assert first["families"]["hover-card"]["javascript"]["raw"] > 0
    assert first["families"]["menu"]["javascript"]["raw"] > 0
    assert first["families"]["navigation-menu"]["javascript"]["raw"] > 0
    assert first["families"]["carousel"]["javascript"]["raw"] > 0
    assert first["families"]["toast"]["javascript"]["raw"] > 0
    assert first["families"]["list"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
    assert first["families"]["tree"]["javascript"]["raw"] > 0
    assert first["families"]["listbox"]["javascript"]["raw"] > 0
    assert first["families"]["multi-select"]["javascript"]["raw"] > 0
    assert first["families"]["editable"]["javascript"]["raw"] > 0
    assert first["families"]["disclosure"]["javascript"]["raw"] > 0


def test_shared_secondary_runtime_is_counted_once_per_measured_slice():
    marker = b"cannot replace an incompatible anchored-layer runtime"
    popover_js, _ = _family_assets(frozenset({"CPopover"}))
    mixed_js, _ = _family_assets(frozenset({"CPopover", "CTooltip", "CMenu"}))

    assert popover_js.count(marker) == 1
    assert mixed_js.count(marker) == 1
