from citry_ui.quality.asset_report import asset_report


def test_asset_report_is_deterministic_and_covers_every_family():
    first = asset_report()
    second = asset_report()

    assert first == second
    assert list(first["families"]) == [
        "button",
        "field-input",
        "form",
        "tabs",
        "dialog",
        "combobox",
        "table",
    ]
    assert first["catalog"]["javascript"]["brotli"] <= 45 * 1024
    assert first["catalog"]["css"]["brotli"] <= 30 * 1024
    assert first["families"]["table"]["javascript"] == {"raw": 0, "gzip": 0, "brotli": 0}
